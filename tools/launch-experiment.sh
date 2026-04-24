#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <experiment-id> [--allow-dirty]" >&2
  exit 2
}

die() {
  echo "error: $*" >&2
  exit 1
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

parse_data_paths() {
  python3 - "$1" <<'PY'
import ast, re, sys
path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
for i, line in enumerate(lines):
    if re.match(r"^\s*#?\s*data_paths\s*:", line):
        value = line.split(":", 1)[1].strip()
        if value.startswith("#"):
            sys.exit(0)
        if value:
            try:
                parsed = ast.literal_eval(value)
            except Exception:
                parsed = []
            for item in parsed if isinstance(parsed, list) else []:
                print(item)
            sys.exit(0)
        base_indent = len(line) - len(line.lstrip())
        for nxt in lines[i + 1:]:
            stripped = nxt.strip()
            indent = len(nxt) - len(nxt.lstrip())
            if not stripped or stripped.startswith("#"):
                continue
            if indent <= base_indent:
                sys.exit(0)
            match = re.match(r"^-\s*(.+?)\s*$", stripped)
            if match:
                print(match.group(1).strip("\"'"))
        sys.exit(0)
PY
}

[[ $# -ge 1 && $# -le 2 ]] || usage

experiment_id="$1"
allow_dirty=false
if [[ $# -eq 2 ]]; then
  [[ "$2" == "--allow-dirty" ]] || usage
  allow_dirty=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "${SCRIPT_DIR}/.." rev-parse --show-toplevel)"
EXP_DIR="${REPO_ROOT}/experiments/${experiment_id}"

[[ -d "$EXP_DIR" ]] || die "missing experiments/${experiment_id}"
[[ -f "${EXP_DIR}/experiment.yaml" ]] || die "missing experiment.yaml"
[[ -f "${EXP_DIR}/config.yaml" ]] || die "missing config.yaml"
[[ ! -e "${EXP_DIR}/launch_manifest.json" ]] || die "launch_manifest.json already exists"
grep -qx 'status: planned' "${EXP_DIR}/experiment.yaml" || die "experiment.yaml status must be planned"

cd "$EXP_DIR"

data_paths=()
while IFS= read -r path; do
  data_paths+=("$path")
done < <(parse_data_paths "config.yaml")
[[ ${#data_paths[@]} -gt 0 ]] || die "config.yaml data_paths is empty"

missing=()
for path in "${data_paths[@]}"; do
  [[ -s "$path" ]] || missing+=("$path")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  printf 'error: unreachable or empty data_paths from %s:\n' "$EXP_DIR" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

dirty_paths="$(git -C "$REPO_ROOT" status --porcelain)"
git_dirty=false
if [[ -n "$dirty_paths" ]]; then
  git_dirty=true
  if [[ "$allow_dirty" != true ]]; then
    echo "error: git tree is dirty; pass --allow-dirty to record it" >&2
    echo "$dirty_paths" >&2
    exit 1
  fi
fi

git_sha="$(git -C "$REPO_ROOT" rev-parse HEAD)"
if [[ ! -s CORE_COMMIT ]]; then
  printf '%s\n' "$git_sha" > CORE_COMMIT
fi
core_commit="$(tr -d '\n' < CORE_COMMIT)"
python_version="$(python3 -c 'import platform; print(platform.python_version())')"
config_sha256="$(sha256_file config.yaml)"
requirements_hash=null
if [[ -f requirements.lock ]]; then
  requirements_hash="$(json_escape "$(sha256_file requirements.lock)")"
fi

{
  printf '{\n'
  printf '  "experiment_id": %s,\n' "$(json_escape "$experiment_id")"
  printf '  "launched_at": %s,\n' "$(json_escape "$(date -u '+%Y-%m-%dT%H:%M:%SZ')")"
  printf '  "git_sha": %s,\n' "$(json_escape "$git_sha")"
  printf '  "git_dirty": %s,\n' "$git_dirty"
  printf '  "python_version": %s,\n' "$(json_escape "$python_version")"
  printf '  "core_commit": %s,\n' "$(json_escape "$core_commit")"
  printf '  "config_sha256": %s,\n' "$(json_escape "$config_sha256")"
  printf '  "requirements_lock_sha256": %s,\n' "$requirements_hash"
  printf '  "data_paths": [\n'
  for i in "${!data_paths[@]}"; do
    comma=','; [[ "$i" -eq $((${#data_paths[@]} - 1)) ]] && comma=''
    printf '    %s%s\n' "$(json_escape "${data_paths[$i]}")" "$comma"
  done
  printf '  ],\n'
  printf '  "data_sha256": {\n'
  for i in "${!data_paths[@]}"; do
    comma=','; [[ "$i" -eq $((${#data_paths[@]} - 1)) ]] && comma=''
    printf '    %s: %s%s\n' "$(json_escape "${data_paths[$i]}")" "$(json_escape "$(sha256_file "${data_paths[$i]}")")" "$comma"
  done
  printf '  },\n'
  printf '  "path_base": %s\n' "$(json_escape "experiments/${experiment_id}/")"
  printf '}\n'
} > launch_manifest.json

sed -i.bak 's/^status: planned$/status: running/' experiment.yaml
rm -f experiment.yaml.bak

tag_name="exp-${experiment_id}-launch"
existing="$(git -C "$REPO_ROOT" rev-parse -q --verify "refs/tags/${tag_name}^{}" 2>/dev/null || true)"
if [[ -z "$existing" ]]; then
  git -C "$REPO_ROOT" tag -a "$tag_name" -m "launch ${experiment_id}" HEAD
elif [[ "$existing" == "$git_sha" ]]; then
  echo "tag ${tag_name} already at HEAD, skipping"
else
  die "tag ${tag_name} already exists at ${existing}; refusing to move"
fi

echo "launched experiments/${experiment_id}"
echo "manifest: experiments/${experiment_id}/launch_manifest.json"
