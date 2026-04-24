#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <experiment-id>" >&2
  exit 2
}

die() {
  echo "error: $*" >&2
  exit 1
}

[[ $# -eq 1 ]] || usage

experiment_id="$1"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
experiment_dir="${repo_root}/experiments/${experiment_id}"
rel_dir="experiments/${experiment_id}"

[[ -n "$experiment_id" ]] || usage
[[ "$experiment_id" != */* ]] || die "experiment id must not contain /"
[[ ! -e "${experiment_dir}/experiment.yaml" ]] || die "refusing to overwrite ${rel_dir}/experiment.yaml"

mkdir -p "${experiment_dir}/results"

cat > "${experiment_dir}/experiment.yaml" <<YAML
id: ${experiment_id}
modality:          # text | audio | music | video | multimodal
project:           # slug naming the research thread, e.g. text-gemma3-prefix-kv
tags: []           # list of orthogonal tags, e.g. [contrastive-loss, llm-instructions]
status: planned
consequential: true
question:
hypothesis:
parent: null
base_model:
dataset:
core_commit:
compute:
results: {}
headline: TBD
next: TBD
YAML

cat > "${experiment_dir}/README.md" <<'MARKDOWN'
# Experiment

Status: planned

## Question

## Hypothesis

## Method

## Results (pending)

## Learnings (pending)

## Replicate
MARKDOWN

cat > "${experiment_dir}/config.yaml" <<'YAML'
# base_model:
# data_paths:
#   - ../../../path/to/train.jsonl
# train_hparams:
#   steps:
#   batch_size:
# eval:
#   n_probes:
YAML

: > "${experiment_dir}/requirements.lock"
: > "${experiment_dir}/CORE_COMMIT"
: > "${experiment_dir}/results/.gitkeep"

cat > "${experiment_dir}/run.sh" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail

echo "TODO: implement training entrypoint"
BASH
chmod +x "${experiment_dir}/run.sh"

cat > "${experiment_dir}/LEARNINGS.md" <<'MARKDOWN'
# Learnings
MARKDOWN

echo "created ${rel_dir}"
echo "next: tools/launch-experiment.sh ${experiment_id}"




























