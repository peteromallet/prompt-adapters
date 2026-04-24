#!/usr/bin/env bash
# Sync program/ content into site/docs/program/ so MkDocs picks it up.
# TODO: extend to also generate per-experiment pages and filter UI from experiments/*/experiment.yaml.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p site/docs/program

# Program tier: copy canonical markdown from program/ into site/docs/program/.
cp program/STRATEGY.md site/docs/program/strategy.md
cp program/LEARNINGS.md site/docs/program/learnings.md
cp program/ROADMAP.md site/docs/program/roadmap.md

# Project tier: copy each project's LEARNINGS into site/docs/projects/<slug>-learnings.md if present.
if [[ -d projects ]]; then
  for proj_dir in projects/*/; do
    slug="$(basename "$proj_dir")"
    if [[ -f "$proj_dir/LEARNINGS.md" ]]; then
      cp "$proj_dir/LEARNINGS.md" "site/docs/projects/${slug}-learnings.md"
    fi
  done
fi

echo "synced program/ → site/docs/program/"
echo "synced projects/*/LEARNINGS.md → site/docs/projects/"
echo "TODO: per-experiment page generation from experiments/<id>/experiment.yaml + README.md"
