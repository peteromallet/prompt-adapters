#!/usr/bin/env bash
# Exact command for experiment 2026-05-text-006-projector-no-trunk.
set -euo pipefail
cd /workspace/text-ip-adapter

HF_HUB_ENABLE_HF_TRANSFER=1 python scripts/train.py \
  --config configs/stage1_gemma_no_trunk.yaml
