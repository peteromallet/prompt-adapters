#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/../../../text-ip-adapter"

PYENV_VERSION=3.11.11 PYTHONPATH=src:../runpod-lifecycle/src python scripts/eval_checkpoint_runpod.py \
  --config configs/stage1_v3_3_corrected_poetry_core3_smoke.yaml \
  --checkpoint checkpoints/stage1_v3_3_corrected_poetry_core3_smoke/final.pt \
  --probe-path data/pairs_v3_3_corrected_poetry_core3/probes_balanced_n15.jsonl \
  --val-path data/pairs_v3_3_corrected_poetry_core3/val.jsonl \
  --local-output-dir ../prompt-adapters/experiments/2026-05-text-015-decoding-repetition-diagnostic/results/runpod_eval \
  --remote-output-dir /workspace/text-ip-adapter/eval_runs/2026-05-text-015-decoding-repetition-diagnostic \
  --variants greedy_no_repeat,sampled_rep \
  --max-new-tokens 120 \
  --step-tag 1500
