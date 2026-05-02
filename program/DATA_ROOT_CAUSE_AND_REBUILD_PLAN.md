# Data root cause and rebuild plan

Generated: 2026-04-25.

## Bottom line

The current bottleneck is not architecture. Fallback 008b proved the no-trunk
warmstart plus active contrastive recipe can recover non-collapsed K/V
conditioning on the bundle (`mean_cos_K_first_swap=0.371`).

The blocker is data construction. We found three independent data failures:

1. v2 speech source is wrong for the objective.
2. old Miller Center speech author extraction was broken but repairable.
3. v2 split policy can leave registers absent from held-out splits.

Do not launch another canonical GPU experiment until a v3 corpus passes data
gates.

## Root causes

### 1. v2 speech source mismatch

`data/sources_v2/canonical/speech.jsonl` contains 60,000 docs from
`Eugleo/us-congressional-speeches` under the `un_debate` label. The intended
Harvard Dataverse UN debate source was skipped because it required guestbook
auth.

The resulting training rows are congressional floor fragments with authors like
`mr_heatwole`, `ir_butler_of_massachusetts`, and `air_hale_of_maine`. This is a
different register from the intended public-speech style transfer task.

### 2. Miller Center speech parser bug

The old 1x/10x speech path used Miller Center pages, but every cached page was
labeled `washington`. The parser fell back to the first global navigation
`/president/washington` anchor when page-local metadata was absent.

Patch applied in `text-ip-adapter/src/text_ip_adapter/data/ingest_speeches.py`:

- infer president from the Miller Center speech URL date using a presidential
  term table;
- stop using global nav `/president/*` anchors as page metadata.

Validation on the existing pod cache:

- before patch: 1000 records, 1 author (`washington`)
- after patch: 998 records, 42 authors

Pair potential after patch:

| speech cap per author | total pairs | train | val | test |
| ---: | ---: | ---: | ---: | ---: |
| 15 | 627 | 507 | 60 | 60 |
| 30 | 1,242 | 1,002 | 120 | 120 |
| 40 | 1,642 | 1,322 | 160 | 160 |
| 50 | 2,034 | 1,634 | 200 | 200 |
| 75 | 2,987 | 2,387 | 300 | 300 |

Speech scarcity is therefore not real at the next experiment scale.

### 3. Split policy warning instead of failing

`prompt-adapters/scripts_staging/make_pairs.py` uses a global author split and
only prints a warning if a register has too few val/test rows. The current
`v2_bundle` has:

- train screenplay: 1,008 rows
- val screenplay: 0 rows
- test screenplay: 0 rows

This invalidates normal held-out evaluation for screenplay.

### 4. Bundle train-only anchor mix-in

`v2_bundle` train includes `006_anchor` rows:

- poetry: 1,698
- screenplay: 1,008
- essay: 162
- speech: 45

Val/test do not have equivalent anchor coverage. This makes 008b a salvage test
only; it cannot measure clean v2 generalization.

## Rebuild contract

Create `data/pairs_v3/` only if these gates pass:

- speech train >= 1,500 pairs
- speech val >= 100 pairs
- speech test >= 100 pairs
- speech authors >= 30
- every scoped register appears in train/val/test
- val/test each have >= 50 pairs per scoped register
- no `(register, author)` overlap across train/val/test
- source_dataset is present on every pair
- instruction policy is consistent across train/val/test

Recommended first v3 scope:

- speech: fixed Miller Center, cap 50
- screenplay: old IMSDb or v2 `dracor`, but only if val/test gates pass
- poetry: keep current best source, but audit obvious language/title leakage
- essay: prefer clean Gutenberg essays for canonical style; use Medium only if
  explicitly labeled as blog/prose and filtered

## Next experiment

`2026-05-text-009-v3-data-rebuild-speechfix` is the next valid step. It is a
CPU-only data experiment. No GPU training should happen until it passes.

## 2026-04-25 v3 candidate result

The CPU-only v3 builder now passes hard gates.

Candidate files are persisted under
`prompt-adapters/experiments/2026-05-text-009-v3-data-rebuild-speechfix/results/v3_candidate/`.

| split | rows | poetry | essay | screenplay | speech |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 10,730 | 2,944 | 144 | 5,708 | 1,934 |
| val | 310 | 100 | 100 | 60 | 50 |
| test | 310 | 100 | 100 | 60 | 50 |

All hard gates pass:

- author-disjoint train/val/test
- `source_dataset` present
- every scoped register appears in val/test
- speech train >= 1,500

Caveat: held-out author counts are sparse for poetry/essay/speech. Treat this
as a launchable next training corpus and use separate, carefully sampled n>=20
probes for final style judgment.
