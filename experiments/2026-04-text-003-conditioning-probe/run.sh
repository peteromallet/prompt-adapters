#!/usr/bin/env bash
# Exact command used to run experiment 003 (formerly 002b, the conditioning probe) conditioning probe (diagnostic, no training).
# Assumes: text-ip-adapter repo checked out at SHA f3dc198, synced to /workspace/text-ip-adapter
# on a RunPod RTX 4090 with Python 3.11.10 + transformers 5.6.2, base model downloadable from HF
# via HF_TOKEN, and experiment 002's final.pt checkpoint exists at the path below.
set -euo pipefail

cd /workspace/text-ip-adapter

python scripts/probe_conditioning.py \
  --checkpoint checkpoints/stage1_gemma_llm/final.pt \
  --config configs/stage1_gemma_llm.yaml \
  --probes data/pairs/probes_n20_llm.jsonl \
  --output-dir results_probe_002b \
  --n-probes 10 \
  --max-new-tokens 80
