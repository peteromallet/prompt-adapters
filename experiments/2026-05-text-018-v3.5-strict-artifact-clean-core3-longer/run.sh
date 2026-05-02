#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/../../../text-ip-adapter"

./scripts/launch_runpod_host.sh --config configs/stage1_v3_5_artifact_clean_core3_longer.yaml
