# Learnings

Status: completed on 2026-04-25.

## Bottom Line

v3.3 core3 is pathway-positive but generation-quality-negative. Do not run a
full v3.3 training run.

The audit found a deeper root cause than expected: many poetry expansion
entries pointed to the wrong Gutenberg books. This explains why poetry probes
could look like geography indexes, school-reader catalogs, German prose,
vivisection statistics, or novels while still carrying `register=poetry`.

## What Changed

- Corrected or removed bogus Gutenberg poetry IDs in `ingest_poetry.py`.
- Added an audit blocklist path to `build_v3_pairs.py`.
- Added reference-side suspicious filtering, not just target-side filtering.
- Added poetry apparatus filters for edition notes, indexes, title pages,
  catalogs, biography snippets, and commentary.
- Built `data/pairs_v3_3_corrected_poetry_core3` with poetry, screenplay, and
  speech only.

## Why Essay Is Excluded

Essay is not declared solved. It is excluded because the clean pool is too
small after audit deletes. Keeping essay in the next smoke would either starve
train or weaken heldout. Essay needs source expansion as a separate data task.

## Result

The 1,500-step smoke completed.

Pathway stayed healthy:

- `mean_cos_K_last_swap=0.398`
- `mean_cos_K_last_random=-0.039`
- `mean_cos_K_last_code=0.044`
- `mean_gen_jaccard_swap=0.036`

Qualitative samples are still not good enough:

- poetry is now verse-shaped but repeats phrases;
- screenplay has screenplay structure but repeats local beats;
- speech has formal address structure but repeats sentences;
- no-ref remains generic summary/repetition.

This separates two hypotheses cleanly: source corruption was real, but it was
not the only blocker. The adapter pathway is alive; the current objective and
generation setup still lead to repetitive outputs.

## Next

Keep the corrected v3.3 core3 data. The next experiment should be an
objective/decoding ablation, not a full run:

1. same corrected core3 corpus;
2. smaller probe set to reduce startup/sample latency;
3. `contrastive_weight=0` ablation for 500-1000 steps;
4. compare repetition and pathway metrics against 013.

If the ablation still repeats, move to target-window/instruction/decoding
interventions rather than more corpus cleaning.
