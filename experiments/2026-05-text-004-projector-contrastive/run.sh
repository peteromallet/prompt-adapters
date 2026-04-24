#!/usr/bin/env bash
# Exact command for experiment 2026-05-text-004-projector-contrastive.
# Runs on the RunPod 4090 after text-ip-adapter is synced to /workspace/text-ip-adapter.
set -euo pipefail
cd /workspace/text-ip-adapter

HF_HUB_ENABLE_HF_TRANSFER=1 python scripts/train.py \
  --config configs/stage1_gemma_contrastive.yaml
