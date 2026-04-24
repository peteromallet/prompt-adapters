#!/usr/bin/env bash
set -euo pipefail
usage() {
  echo "usage: $0 <experiment-id> [--hypothesis-outcome V] [--surprises V] [--corrections V] [--next-experiment V] [--rolls-up-project true|false] [--rolls-up-program true|false]" >&2
  exit 2
}
die() {
  echo "error: $*" >&2
  exit 1
}
prompt_text() {
  local var_name="$1"
  local prompt="$2"
  local current="${!var_name}"
  if [[ -z "$current" ]]; then
    read -r -p "$prompt: " current
    printf -v "$var_name" '%s' "$current"
  fi
}
prompt_bool() {
  local var_name="$1"
  local prompt="$2"
  local current="${!var_name}"
  if [[ -z "$current" ]]; then
    read -r -p "$prompt [y/N]: " current
    case "$current" in
      y|Y|yes|YES|true) current=true ;;
      *) current=false ;;
    esac
    printf -v "$var_name" '%s' "$current"
  fi
}
experiment_id=""
hypothesis_outcome=""
surprises=""
corrections=""
next_experiment=""
rolls_up_project=""
rolls_up_program=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hypothesis-outcome)
      [[ $# -ge 2 ]] || usage
      hypothesis_outcome="$2"
      shift 2
      ;;
    --surprises)
      [[ $# -ge 2 ]] || usage
      surprises="$2"
      shift 2
      ;;
    --corrections)
      [[ $# -ge 2 ]] || usage
      corrections="$2"
      shift 2
      ;;
    --next-experiment)
      [[ $# -ge 2 ]] || usage
      next_experiment="$2"
      shift 2
      ;;
    --rolls-up-project)
      [[ $# -ge 2 ]] || usage
      rolls_up_project="$2"
      shift 2
      ;;
    --rolls-up-program)
      [[ $# -ge 2 ]] || usage
      rolls_up_program="$2"
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "${SCRIPT_DIR}/.." rev-parse --show-toplevel)"
EXP_DIR="${REPO_ROOT}/experiments/${experiment_id}"
YAML_PATH="${EXP_DIR}/experiment.yaml"
LEARNINGS_PATH="${EXP_DIR}/LEARNINGS.md"
[[ -f "$YAML_PATH" ]] || die "missing experiments/${experiment_id}/experiment.yaml"
grep -qx 'status: finalized' "$YAML_PATH" || die "experiment.yaml status must be finalized"
[[ -f "$LEARNINGS_PATH" ]] || die "missing LEARNINGS.md"
learn_bytes="$(wc -c < "$LEARNINGS_PATH" | tr -d ' ')"
[[ "$learn_bytes" -ge 400 ]] || die "LEARNINGS.md must be at least 400 bytes"
! grep -q '^reflection:' "$YAML_PATH" || die "experiment already has reflection"
prompt_text hypothesis_outcome "hypothesis outcome (confirmed|partially_confirmed|refuted|unclear)"
prompt_text surprises "surprises"
prompt_text corrections "corrections to prior beliefs"
prompt_text next_experiment "next experiment id or none"
prompt_bool rolls_up_project "rolls up to project"
prompt_bool rolls_up_program "rolls up to program"
case "$hypothesis_outcome" in
  confirmed|partially_confirmed|refuted|unclear) ;;
  *) die "hypothesis outcome must be one of: confirmed, partially_confirmed, refuted, unclear" ;;
esac
case "$rolls_up_project" in
  true|false) ;;
  *) die "--rolls-up-project must be true or false" ;;
esac
case "$rolls_up_program" in
  true|false) ;;
  *) die "--rolls-up-program must be true or false" ;;
esac
[[ -n "$next_experiment" ]] || die "next_experiment must be non-empty"
python3 - "$YAML_PATH" "$hypothesis_outcome" "$surprises" "$corrections" "$next_experiment" "$rolls_up_project" "$rolls_up_program" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
outcome, surprises, corrections, next_exp, rolls_project, rolls_program = sys.argv[2:]
def literal(value):
    lines = value.splitlines() or [""]
    return "\n".join(f"    {line}" if line else "    " for line in lines)
block = f"""
reflection:
  hypothesis_outcome: {outcome}
  surprises: |
{literal(surprises)}
  corrections_to_prior_beliefs: |
{literal(corrections)}
  next_experiment: {next_exp}
  rolls_up_to_project: {rolls_project}
  rolls_up_to_program: {rolls_program}
"""
with path.open("a", encoding="utf-8") as fh:
    fh.write(block)
PY
sed -i.bak 's/^status: finalized$/status: closed/' "$YAML_PATH"
rm -f "${YAML_PATH}.bak"
if [[ "$next_experiment" != "none" ]]; then
  "${REPO_ROOT}/tools/plan-experiment.sh" "$next_experiment"
  next_yaml="${REPO_ROOT}/experiments/${next_experiment}/experiment.yaml"
  sed -i.bak "s/^parent: null$/parent: ${experiment_id}/" "$next_yaml"
  rm -f "${next_yaml}.bak"
fi
project_slug="$(awk -F': *' '$1 == "project" {print $2; exit}' "$YAML_PATH" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
headline="$(awk -F': *' '$1 == "headline" {sub(/^"/, "", $2); sub(/"$/, "", $2); print $2; exit}' "$YAML_PATH")"

# Auto-write structured rollup entries to project/program LEARNINGS.md.
# Operator can still edit further afterward; the script just writes the
# baseline "[<id>] <headline>" pointer so nothing is silently lost.
write_rollup_entry() {
  local target="$1"
  local label="$2"
  local entry="- **[${experiment_id}](../experiments/${experiment_id}/) — ${hypothesis_outcome}**: ${headline}"
  if grep -qF "${experiment_id}" "$target" 2>/dev/null; then
    echo "[close] ${label} already references ${experiment_id}; skipping append"
  else
    {
      echo ""
      echo "## Auto-rollup ($(date -u '+%Y-%m-%d'))"
      echo ""
      echo "$entry"
    } >> "$target"
    echo "[close] appended rollup entry to ${target}"
  fi
}

if [[ "$rolls_up_project" == true ]]; then
  proj_learnings="${REPO_ROOT}/projects/${project_slug}/LEARNINGS.md"
  if [[ -f "$proj_learnings" ]]; then
    write_rollup_entry "$proj_learnings" "project LEARNINGS"
  else
    echo "warn: ${proj_learnings} missing — skipping project rollup"
  fi
  if [[ -n "${EDITOR:-}" ]]; then
    "$EDITOR" "$proj_learnings"
  fi
fi
if [[ "$rolls_up_program" == true ]]; then
  prog_learnings="${REPO_ROOT}/program/LEARNINGS.md"
  write_rollup_entry "$prog_learnings" "program LEARNINGS"
  if [[ -n "${EDITOR:-}" ]]; then
    "$EDITOR" "$prog_learnings"
  fi
fi

# Update ROADMAP.md status for this experiment row, if it exists.
roadmap="${REPO_ROOT}/program/ROADMAP.md"
if [[ -f "$roadmap" ]] && grep -qF "${experiment_id}" "$roadmap"; then
  python3 - "$roadmap" "$experiment_id" "$hypothesis_outcome" "$headline" <<'PY'
import re, sys
path, eid, outcome, headline = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
text = open(path).read()
# Find any markdown table row containing the experiment id and replace the
# Status column content with "closed — <outcome>" if it currently mentions
# planned/running/finalized/queued.
lines = text.splitlines()
changed = False
for i, line in enumerate(lines):
    if eid in line and line.lstrip().startswith("|"):
        if any(tok in line for tok in ("planned", "running", "finalized", "queued", "(next)", "TBD")):
            new = re.sub(r"\*\*?(planned|running|finalized|queued|planned \(next\))[^|]*\*?\*?",
                         f"**closed — {outcome}**", line, count=1)
            if new == line:
                # fallback: replace the third-to-last cell (status column heuristic).
                pass
            else:
                lines[i] = new
                changed = True
                break
if changed:
    open(path, 'w').write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    print(f"[close] updated ROADMAP row for {eid}")
else:
    print(f"[close] ROADMAP row for {eid} not auto-updated; review manually")
PY
fi
git_sha="$(git -C "$REPO_ROOT" rev-parse HEAD)"
tag_name="exp-${experiment_id}-closed"
existing="$(git -C "$REPO_ROOT" rev-parse -q --verify "refs/tags/${tag_name}^{}" 2>/dev/null || true)"
if [[ -z "$existing" ]]; then
  git -C "$REPO_ROOT" tag -a "$tag_name" -m "closed ${experiment_id}" HEAD
elif [[ "$existing" == "$git_sha" ]]; then
  echo "tag ${tag_name} already at HEAD, skipping"
else
  die "tag ${tag_name} already exists at ${existing}; refusing to move"
fi
echo "closed experiments/${experiment_id}"
