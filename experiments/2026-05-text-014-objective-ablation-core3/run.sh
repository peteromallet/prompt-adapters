#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/../text-ip-adapter"

./scripts/launch_runpod_host.sh --config configs/stage1_v3_3_core3_no_contrastive_smoke.yaml
