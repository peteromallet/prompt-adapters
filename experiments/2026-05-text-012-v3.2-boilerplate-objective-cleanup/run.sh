#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/../text-ip-adapter"

PYTHONPATH=src python scripts/build_v3_pairs.py \
  --data-root data \
  --output-dir data/pairs_v3_2 \
  --instruction-mode content_style_no_theme \
  --clean-boilerplate \
  --filter-suspicious-targets \
  --min-heldout-per-register 50 \
  --min-heldout-authors-per-register 2 \
  --speech-train-min 1200 \
  --min-train-pairs poetry=1500 \
  --min-train-pairs essay=80 \
  --min-train-pairs screenplay=1500 \
  --write-balanced-probes
