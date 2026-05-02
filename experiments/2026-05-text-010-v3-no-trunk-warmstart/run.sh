#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/../text-ip-adapter"

PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python scripts/train.py \
  --config configs/stage1_v3_no_trunk_warmstart.yaml
