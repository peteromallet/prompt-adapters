# Data Lineage Audit - v2 and bundle fallback

Generated: 2026-04-25 during the 008/008b pod run.

## Question

Are we missing data, or did the data build produce the wrong held-out shape?

Answer: the files are not missing. The source corpus exists on the pod, but the
v2 source choices and split policy are misaligned with the experiment goal.

## Pod source files

Canonical source files found under `/workspace/text-ip-adapter/data/sources_v2/canonical/`:

| file | docs | authors | eligible authors >=2 | source dataset |
| --- | ---: | ---: | ---: | --- |
| `essay.jsonl` | 80,000 | 37,643 | 12,049 | `medium` |
| `poetry.jsonl` | 43,582 | 4,220 | 2,333 | `pulpo` |
| `screenplay.jsonl` | 5,383 | 60 | 60 | `dracor` |
| `speech.jsonl` | 60,000 | 6,627 | 1,857 | `un_debate` |

Raw source logs:

- speech: `count=60000 skipped=206353 unique_authors=6627`; only
  `Eugleo/us-congressional-speeches` was used. The intended Harvard Dataverse
  UN debate source was skipped because it required guestbook auth.
- screenplay: `count=5383 skipped=141 total_authors=60 eligible_authors=60`.
- essay: `count=80000 skipped=16755 unique_authors=37643`.

## Correction to the first quick audit

The pair rows do carry `source_dataset`; an earlier ad hoc display checked
`source` before `source_dataset` and printed `<missing>`. The corrected audit
shows:

- v2 poetry: `pulpo`
- v2 essay: `medium`
- v2 screenplay: `dracor`
- v2 speech: `un_debate`
- v2 bundle train mix-in: `006_anchor`

So the issue is not missing source metadata in the pair rows. The issue is
source choice, source quality, split behavior, and the bundle's train-only
anchor mix-in.

## What is actually wrong

### Speech is not the intended style source

`v2_clean` speech is mostly congressional floor fragments with OCR-like speaker
slugs (`mr_*`, `ir_*`, `air_*`) and text such as committee motions, objections,
petitions, and chamber dialogue. It is not the Miller Center presidential speech
style source used in the original 1x/10x path.

The curation filter correctly deletes most rows matching `mr_*` plus
`un_debate`, but that reveals the source problem:

- before curation: speech has 3,297 rows across all splits
- after curation: speech has 462 rows across all splits
- AG2 fails because speech falls below the 1,500-pair must gate and the
  1,000-pair stop threshold

This is not a small cleanup miss. The speech register was built from the wrong
kind of speech for this experiment.

### Screenplay held-out coverage is a split-policy artifact

The builder at `prompt-adapters/scripts_staging/make_pairs.py` uses a global
author split and then only warns if a register has too few val/test rows:

- `split_authors()` assigns authors 90/5/5 globally.
- `make_pairs.py` logs per-register split counts.
- If val/test has fewer than 50 rows for a register, it prints a warning but
  does not rebalance or backfill.

Because screenplay has only 60 eligible authors in the v2 source, held-out
coverage is fragile. The current `v2_bundle` fallback has:

- train: 1,008 screenplay rows
- val: 0 screenplay rows
- test: 0 screenplay rows

That means `v2_bundle` can train on screenplay but cannot evaluate held-out
screenplay behavior through the normal val/test path.

### Essay quality is broad but noisy

The essay source is Medium. It has many authors and rows, but the v2 curation
removed a large fraction for non-literary web/listicle/support/code scaffolding:

- removed `essay_non_literary_scaffolding`: 3,460 rows
- curated essay rows across all splits: 2,240

This is launchable only if we treat essay as broad blog/prose style rather than
classical essay style. It is not equivalent to the old curated essay register.

### `v2_bundle` is a salvage test, not a clean corpus

The bundle data improves row count by combining generic-instruction material
with older/literary sources, but it is confounded:

- all bundle instructions are the generic
  `Write a piece in the style of the reference passage.`
- train includes screenplay, but val/test omit screenplay
- train includes `006_anchor` rows: 1,698 poetry, 1,008 screenplay, 162 essay,
  and 45 speech rows; val/test do not carry equivalent anchor coverage
- speech remains heavily congressional-style, though row count is usable
- it changes data, instruction style, target length, batch size, and active
  contrastive pressure together

So the current low-memory bundle run can answer "is this pathway salvageable at
all?" It cannot cleanly validate v2 as a high-quality corpus.

## Current experiment impact

The original 008 minfix was correctly blocked by the pre-flight corpus gate.
Running it would have trained on a hollow curated speech register.

The active run is therefore fallback 008b:

- config: `/workspace/text-ip-adapter/configs/stage1_v2_bundle_lowmem.yaml`
- checkpoint dir: `/workspace/text-ip-adapter/checkpoints/stage1_v2_bundle_lowmem`
- data: `data/pairs_v2/*.v2_bundle.jsonl`
- reason: cheap salvage test after `stage1_v2_bundle.yaml` OOM'd at
  `reference_max=1024`, `target_max=1024`, `batch_size=2`

As of the audit, training is alive and has written `step_1000.pt`; the
step-1000 GPU probe was deferred because probing during training caused OOM.

## Next data fix if 008b is worth continuing

Additional root cause found after 008b:

The old Miller Center speech path was also broken, but repairable. Cached Miller
pages were all labeled `washington` because the parser fell back to the first
global navigation `/president/washington` anchor. After patching
`text_ip_adapter.data.ingest_speeches` to infer president from the speech URL
date and ignore global nav anchors, the existing pod cache yields 998 speech
records across 42 presidents. With per-author pair cap 50, this gives 2,034
speech pairs split as train=1,634, val=200, test=200.

1. Rebuild speech from a style-appropriate source:
   - prefer Miller Center presidential speeches from the existing
     `text-ip-adapter/src/text_ip_adapter/data/ingest_speeches.py`, or
   - use congressional data only after speaker/title cleanup and explicit
     debate-register labeling.
2. Replace global author split with per-register author split plus hard held-out
   minimums. A build that leaves a register absent from val/test should fail,
   not warn.
3. Keep `source_dataset` visible in all audits and training pairs; do not let
   source lineage disappear into `<missing>` during diagnosis.
4. Generate a new generic-instruction or LLM-instruction corpus consistently,
   instead of mixing rule-generated topical instructions and generic style
   instructions across variants.
5. Re-run the audit gates before any canonical v2 training:
   - at least 1,500 rows each for poetry/essay/speech after curation
   - screenplay present in train/val/test, or explicitly removed from the
     experiment's evaluation scope
   - no author overlap across splits within each register
