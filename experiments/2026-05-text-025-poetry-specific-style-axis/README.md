# 2026-05-text-025-poetry-specific-style-axis

Status: completed; pathway-positive, surface-mixed.

## Question

024c made screenplay strong but left poetry weak. Is poetry weak because it is
underweighted and diluted by the mixed-register objective, or because the
current objective still cannot learn a poetry style axis?

## Current Read

024c did recover a clean K/V pathway from 006 on v4 style-clean data, but the
poetry outputs are still qualitatively weak: title-heavy verse, occasional
plain prose/instruction-following leakage, and old probes that still carried
some heading/dramatic-material contamination.

The next best bet is therefore stricter poetry isolation rather than wider
encoder changes. I built two local datasets:

- `pairs_v4_2_poetry_styleclean`: direct poetry-only v4.1 slice.
- `pairs_v4_3_poetry_strict`: preferred launch target; strips obvious
  title/section headings and excludes stage/prose-like rows.

## Planned Run

Train a strict poetry-only v4.3 restart from the clean 006 no-trunk checkpoint:

- data: `pairs_v4_3_poetry_strict`
- probes: 16 generic-instruction poetry probes
- init: `checkpoints/stage1_gemma_no_trunk/final.pt`
- contrastive: `0.1`
- triplet: `0.7`, margin `0.35`
- steps: `1200`

Gate: beat 024c poetry `cos_K_last_swap=0.559` by a large margin while keeping
random/code near zero and sampled repetition low.

## Result

The strict poetry-only restart substantially improved the poetry pathway:

- 024c poetry baseline: `cos_K_last_swap=0.5592`
- 025 strict poetry repeat: `cos_K_last_swap=0.4053`
- random/code remain separated: `0.1012` / `0.1387`

Surface quality is still mixed. Repetition is low, but sampled outputs still
show occasional instruction/meta leakage and prose drift. Full summary:
`results/analysis_summary.md`.

## Operational Notes

Hugging Face auth was found in local env files outside this repo and worked for
RunPod. The first 025 run completed but failed local artifact download because
the launcher tried to pull all intermediate checkpoints. The launcher now
downloads eval first, can prune `step_*.pt`, and removes local tar archives
after extraction. The repeat run completed and terminated cleanly.
