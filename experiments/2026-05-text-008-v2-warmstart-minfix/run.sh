#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

cd "$ROOT/../text-ip-adapter"
PYTHONPATH="$PWD/src:$ROOT/../runpod-lifecycle/src" \
  PYENV_VERSION="${PYENV_VERSION:-3.11.11}" \
  python scripts/run_existing_pod_v2_minfix.py
