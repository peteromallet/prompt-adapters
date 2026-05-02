# Learnings

## Pre-flight outcome: blocked by corpus audit

The pod-side v2 curation audit failed before experiment 008 became a valid
training experiment.

Gate results from `results/audit_v2_curated.json`:

- AG1: fail (`ag1_survival_fraction = 0.585`, below 0.60)
- AG2: fail (speech survives at 462 rows, below the 1500 must gate and below
  the 1000 stop threshold)
- AG3: pass (author-disjoint splits remain clean)

The removals identify the v2 problem directly:

- `essay_non_literary_scaffolding`: 3460 rows removed
- `speech_mr_un_debate`: 2835 rows removed

Training briefly started because the runner launched after curation, but it was
killed once the failed audit gates were inspected. Treat this as a pre-flight
abort, not as a model result.

## Next

Do not run `stage1_v2_warmstart_minfix.yaml` on the current curated v2 corpus.
The next valid move is either:

1. fall back to a previously cleaned 10x corpus with adequate speech coverage,
   or
2. rebuild/regenerate the v2 speech and essay sources, then rerun the audit
   before any GPU launch.

## Follow-up lineage audit

See `results/data_lineage_audit.md`.

The pod is not missing source files. The failure is lineage and split policy:

- v2 speech was built from `Eugleo/us-congressional-speeches` under the
  `un_debate` source label after the intended Harvard Dataverse source was
  skipped for guestbook auth. The resulting rows are mostly congressional
  speaker fragments (`mr_*`, `ir_*`, `air_*`), so the curated filter correctly
  removes most of them.
- v2 screenplay has only 60 eligible authors. The v2 pair builder uses a
  global author split and only warns when a register is underrepresented, so
  the current `v2_bundle` has screenplay in train but none in val/test.
- Medium essay volume is high, but much of it is web/blog scaffolding rather
  than clean literary essay style.

The active fallback run is therefore 008b, not canonical 008: it is a cheap
salvage probe for the pathway, using `stage1_v2_bundle_lowmem.yaml` after the
full `stage1_v2_bundle.yaml` OOM'd at 1024/1024 context.

## Fallback 008b outcome

See `results/v2_bundle_lowmem_final_summary.md`.

The low-memory bundle fallback completed 5,000 steps and saved
`/workspace/text-ip-adapter/checkpoints/stage1_v2_bundle_lowmem/final.pt`.

Final 20-probe pathway diagnostic:

- swap `mean_cos_z = 0.271`
- swap `mean_cos_K_first = 0.371`
- swap `mean_cos_K_last = 0.384`
- swap `mean_cos_V_first = 0.356`
- swap `mean_cos_V_last = 0.363`
- swap `mean_gen_jaccard = 0.003`

This is a useful salvage result: the pathway is no longer collapsed like v2
dryrun (`cos_K_first_swap=0.989`) or bigctx (`cos_K_first_swap=0.929`), though
it remains weaker than 006 (`cos_K_first_swap=0.221`).

Generation smoke shows the remaining problem: own/swap generations are less
repetitive than zero/random/code, but OOD/no-reference conditions still collapse
often. This is pathway-positive, data-quality-negative evidence. Do not treat it
as clean validation of v2.

Next best bet: stop tuning this v2 corpus and rebuild the data path before the
next canonical training run. The required fix is source lineage plus split
policy, not another learning-rate or context-size tweak.

## Deeper root cause after backtracking

The old Miller Center speech source is repairable. It was not actually scarce:
the parser mislabeled every cached page as `washington` because it used the
first global navigation `/president/washington` link as a fallback. After
patching `ingest_speeches.py` to infer president from the URL date and ignore
global nav anchors, the existing pod cache yields:

- 998 records
- 42 presidents
- 2,034 speech pairs at cap 50
- split counts at cap 50: train 1,634 / val 200 / test 200

This changes the next move from "find a new speech source" to "rebuild v3 with
fixed Miller speech and hard split gates." The next experiment is
`2026-05-text-009-v3-data-rebuild-speechfix`.
