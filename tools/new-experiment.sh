#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <experiment-id>" >&2
  exit 2
fi

experiment_id="$1"
experiment_dir="experiments/${experiment_id}"

if [[ -f "${experiment_dir}/experiment.yaml" ]]; then
  echo "refusing to overwrite ${experiment_dir}/experiment.yaml" >&2
  exit 1
fi

mkdir -p "${experiment_dir}/results"

cat > "${experiment_dir}/experiment.yaml" <<YAML
id: ${experiment_id}
modality:
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
headline:
next:
YAML

cat > "${experiment_dir}/README.md" <<'MARKDOWN'
# Experiment

## Question

## Hypothesis

## Method

## Results

## Learnings

## Replicate
MARKDOWN

cat > "${experiment_dir}/config.yaml" <<'YAML'
# TODO: add experiment configuration.
YAML

: > "${experiment_dir}/requirements.lock"
: > "${experiment_dir}/CORE_COMMIT"
: > "${experiment_dir}/results/.gitkeep"

cat > "${experiment_dir}/run.sh" <<'BASH'
#!/usr/bin/env bash
# TODO: implement training entrypoint
BASH
chmod +x "${experiment_dir}/run.sh"

cat > "${experiment_dir}/LEARNINGS.md" <<'MARKDOWN'
# Learnings
MARKDOWN

echo "created ${experiment_dir}"
