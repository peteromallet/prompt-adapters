#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_FILES = ["experiment.yaml", "config.yaml", "launch_manifest.json",
              "requirements.lock", "LEARNINGS.md", "README.md"]
def yaml_value(text, key):
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", text, re.MULTILINE)
    value = match.group(1).strip() if match else ""
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'" else value
def hf_token():
    path = Path("~/.cache/huggingface/token").expanduser()
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    return path.read_text(encoding="utf-8").strip() if path.exists() else None
def github_base(repo_root):
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repo_root), "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        raw = ""
    if raw.startswith("git@github.com:"):
        raw = "https://github.com/" + raw.split(":", 1)[1]
    return (raw[:-4] if raw.endswith(".git") else raw) or "https://github.com/peteromallet/prompt-adapters"
def upload_items(exp_dir, checkpoint_path):
    items = [(exp_dir / name, Path(name)) for name in BASE_FILES if (exp_dir / name).exists()]
    results_dir = exp_dir / "results"
    if results_dir.exists():
        for path in sorted(results_dir.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                items.append((path, path.relative_to(exp_dir)))
    if checkpoint_path:
        path = Path(checkpoint_path).expanduser()
        if not path.is_file():
            raise SystemExit(f"error: missing checkpoint file: {path}")
        items.append((path, Path("checkpoint") / path.name))
    return items
def write_hf_readme(stage, base_url, experiment_id, project_slug, headline):
    (stage / "README.md").write_text(
        f"# prompt-adapters {project_slug} {experiment_id}\n\n"
        f"Project: [{project_slug}]({base_url}/tree/main/projects/{project_slug})\n"
        f"Experiment: `{experiment_id}`\n\nHeadline result:\n{headline or 'TBD'}\n\n"
        f"Source: {base_url}/tree/main/experiments/{experiment_id}\n",
        encoding="utf-8")
def without_checkpoint(text):
    out = []
    skipping = False
    for line in text.splitlines():
        if re.match(r"^checkpoint:\s*$", line):
            skipping = True
            continue
        if skipping and re.match(r"^[A-Za-z0-9_]+:\s*", line):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    parser.add_argument("--checkpoint-path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    exp_dir = repo_root / "experiments" / args.experiment_id
    if not exp_dir.is_dir():
        print(f"error: missing experiments/{args.experiment_id}", file=sys.stderr)
        return 1
    yaml_path = exp_dir / "experiment.yaml"
    yaml_text = yaml_path.read_text(encoding="utf-8")
    project_slug = yaml_value(yaml_text, "project")
    headline = yaml_value(yaml_text, "headline")
    if not project_slug:
        print("error: experiment.yaml missing project", file=sys.stderr)
        return 1
    repo_id = f"{os.environ.get('HF_NAMESPACE', 'peteromallet')}/prompt-adapters-{project_slug}"
    branch = f"exp-{args.experiment_id}"
    items = upload_items(exp_dir, args.checkpoint_path)
    if args.dry_run:
        print(f"repo_id: {repo_id}\nbranch: {branch}\nuploads:")
        for _, rel in sorted(items, key=lambda item: str(item[1])):
            print(f"  {rel}")
        return 0
    token = hf_token()
    if not token:
        print("error: missing HF_TOKEN and ~/.cache/huggingface/token", file=sys.stderr)
        return 1
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    api.create_branch(repo_id=repo_id, branch=branch, repo_type="model", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        for src, rel in items:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        write_hf_readme(stage, github_base(repo_root), args.experiment_id, project_slug, headline)
        info = api.upload_folder(repo_id=repo_id, repo_type="model", revision=branch,
                                 folder_path=str(stage), commit_message=f"upload {args.experiment_id}")
    revision = getattr(info, "oid", "")
    yaml_path.write_text(
        without_checkpoint(yaml_text)
        + f"checkpoint:\n  hf_repo: {repo_id}\n  hf_branch: {branch}\n  hf_revision_sha: {revision}\n",
        encoding="utf-8")
    print(f"pushed {repo_id}@{branch} {revision}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
