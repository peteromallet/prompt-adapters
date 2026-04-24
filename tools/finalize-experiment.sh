#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <experiment-id> [--push] [--checkpoint-path PATH] [--dry-run]" >&2
  exit 2
}

die() {
  echo "error: $*" >&2
  exit 1
}

results_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    find results -type f | sort | xargs sha256sum | sha256sum | awk '{print $1}'
  else
    find results -type f | sort | xargs shasum -a 256 | shasum -a 256 | awk '{print $1}'
  fi
}

yaml_value() {
  local key="$1"
  awk -F': *' -v k="$key" '$1 == k {print $2; exit}' experiment.yaml \
    | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

experiment_id=""
push=false
dry_run=false
checkpoint_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push)
      push=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --checkpoint-path)
      [[ $# -ge 2 ]] || usage
      checkpoint_path="$2"
      shift 2
      ;;
    -*)
      die "unknown argument: $1"
      ;;
    *)
      [[ -z "$experiment_id" ]] || die "multiple experiment ids provided"
      experiment_id="$1"
      shift
      ;;
  esac
done

[[ -n "$experiment_id" ]] || usage

REPO_ROOT="$(git rev-parse --show-toplevel)"
exp_dir="${REPO_ROOT}/experiments/${experiment_id}"

[[ -d "$exp_dir" ]] || die "missing experiments/${experiment_id}"
cd "$exp_dir"

[[ -f launch_manifest.json ]] || die "missing launch_manifest.json"
[[ -f experiment.yaml ]] || die "missing experiment.yaml"
grep -qx 'status: running' experiment.yaml || die "experiment.yaml status must be running"
[[ -d results ]] || die "missing results/"
if ! find results -type f ! -name '.gitkeep' | grep -q .; then
  die "results/ must contain at least one non-.gitkeep file"
fi
[[ -s LEARNINGS.md ]] || die "LEARNINGS.md must be non-empty"

headline="$(yaml_value headline)"
next_value="$(yaml_value next)"
[[ -n "$headline" && "$headline" != "TBD" ]] || die "experiment.yaml headline must be non-empty and not TBD"
[[ -n "$next_value" && "$next_value" != "TBD" ]] || die "experiment.yaml next must be non-empty and not TBD"

finalized_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
hash="$(results_hash)"

# Auto-populate experiment.yaml `results:` block from results/eval_report.json
# and results/capabilities_analysis.json if either exists. This is the missing
# piece — without it, the operator has to hand-copy verdicts and the rollup
# step (project/program LEARNINGS, ROADMAP) becomes manual every time.
if [[ -f results/eval_report.json || -f results/capabilities_analysis.json ]]; then
  python3 - <<'PY'
import json
import re
from pathlib import Path

def load(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None

ev = load("results/eval_report.json")
cap = load("results/capabilities_analysis.json")
cond = load("results/conditioning_probe_analysis.json")

# Build a results: block we can append (preserve existing if non-empty).
results = {}
if ev:
    for k in ("test1_discrimination", "test2_llm_judge", "test3_style_carryover",
              "test3b_llm_style_match", "test4_memorization", "test5_loss_curve"):
        if k in ev and isinstance(ev[k], dict):
            v = ev[k].get("verdict") or ev[k].get("status")
            note_keys = ("final_mean_jaccard","adapter_win_rate","mean_advantage",
                         "target_memorization_rate","ref_leak_rate","improvement_pct")
            extras = {nk: ev[k].get(nk) for nk in note_keys if nk in ev[k]}
            results[k] = f"{v} ({extras})" if extras else v
if cap:
    ab = cap.get("alpha_blend", {})
    sd = cap.get("strength_dial", {})
    if ab:
        results["capability_alpha_blend"] = (
            f"monotonic_count={ab.get('monotonic_count')}/{cap.get('n_probes')}; "
            f"endpoint_J={ab.get('mean_endpoint_jaccard'):.3f}; "
            f"smoothness_balance={ab.get('mean_smoothness_balance'):.3f}"
        )
    if sd:
        results["capability_strength_dial"] = (
            f"J(λ=0.5,1)={sd.get('mean_j_lam05'):.3f}; "
            f"J(λ=2,1)={sd.get('mean_j_lam2'):.3f}; "
            f"len(λ=2)/len(λ=1)={sd.get('mean_length_at_lam2_vs_lam1'):.2f}"
        )
if cond:
    for k in ("mean_cos_z_swap", "mean_cos_K_first_swap", "mean_cos_K_first_zero",
              "mean_cos_K_first_random", "mean_cos_K_first_code"):
        if k in cond:
            results[k] = round(cond[k], 4)

if not results:
    raise SystemExit(0)

# Read existing experiment.yaml; replace `results: {}` with populated block ONLY if empty.
text = Path("experiment.yaml").read_text()
if re.search(r'^results:\s*\{\s*\}\s*$', text, re.MULTILINE):
    block_lines = ["results:"]
    for k, v in results.items():
        if isinstance(v, (int, float)):
            block_lines.append(f"  {k}: {v}")
        else:
            sv = str(v).replace('"', '\\"')
            block_lines.append(f'  {k}: "{sv}"')
    block_lines.append("  _auto_populated_at: \"" + __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + "\"")
    new_block = "\n".join(block_lines)
    text = re.sub(r'^results:\s*\{\s*\}\s*$', new_block, text, count=1, flags=re.MULTILINE)
    Path("experiment.yaml").write_text(text)
    print("[finalize] auto-populated experiment.yaml results: block from results/*.json")
else:
    print("[finalize] experiment.yaml results: block is non-empty; leaving unchanged")
PY
fi

tmp_manifest="$(mktemp)"
python3 - "$finalized_at" "$hash" launch_manifest.json > "$tmp_manifest" <<'PY'
import datetime as dt
import json
import sys

finalized_at, results_sha256, manifest_path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(manifest_path, encoding="utf-8") as fh:
    manifest = json.load(fh)
finalize = {
    "finalized_at": finalized_at,
    "results_sha256": results_sha256,
}
launched_at = manifest.get("launched_at")
try:
    if launched_at:
        start = dt.datetime.fromisoformat(launched_at.replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(finalized_at.replace("Z", "+00:00"))
        finalize["duration_seconds"] = int((end - start).total_seconds())
except Exception:
    pass
manifest["finalize"] = finalize
json.dump(manifest, sys.stdout, indent=2)
sys.stdout.write("\n")
PY
mv "$tmp_manifest" launch_manifest.json

sed -i.bak 's/^status: running$/status: finalized/' experiment.yaml
rm -f experiment.yaml.bak

git_sha="$(git -C "$REPO_ROOT" rev-parse HEAD)"
tag_name="exp-${experiment_id}-finalized"
existing="$(git -C "$REPO_ROOT" rev-parse -q --verify "refs/tags/${tag_name}^{}" 2>/dev/null || true)"
if [[ -z "$existing" ]]; then
  git -C "$REPO_ROOT" tag -a "$tag_name" -m "finalized ${experiment_id}" HEAD
elif [[ "$existing" == "$git_sha" ]]; then
  echo "tag ${tag_name} already at HEAD, skipping"
else
  die "tag ${tag_name} already exists at ${existing}; refusing to move"
fi

if [[ "$push" == true ]]; then
  push_args=("$experiment_id")
  if [[ -n "$checkpoint_path" ]]; then
    push_args+=(--checkpoint-path "$checkpoint_path")
  fi
  if [[ "$dry_run" == true ]]; then
    push_args+=(--dry-run)
  fi
  python3 "${REPO_ROOT}/tools/hf_push.py" "${push_args[@]}" || exit $?
fi

echo "finalized experiments/${experiment_id}"
echo "replay: inspect experiments/${experiment_id}/launch_manifest.json for pinned inputs and results hash"























