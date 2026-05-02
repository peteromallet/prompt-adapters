# Experiment 011 - v3.1 data/eval repair

Status: completed

## Question

Can we repair the v3 data and evaluation layer enough to reduce the
generic-summary/repetition failure seen in 010 before changing architecture
again?

## Hypothesis

Experiment 010 showed that the no-trunk warmstart pathway is not globally
collapsed, but final generations remain poor. The failure now looks like
data/eval/objective alignment:

- legacy n=20 probes omitted speech entirely;
- the first v3 split has sparse held-out authors for poetry/essay/speech;
- final samples drift into reference-book summaries and repeated stock phrases;
- speech own-vs-swap nearly collapsed on the balanced probe.

If v3.1 removes summary/list/table-of-contents/reference-book targets,
increases held-out author diversity, and makes balanced probes canonical, then
a cheap follow-up run should keep K/V separation while reducing repetitive
generic summaries.

## Method

1. Audit v3 train/val/test for target chunks that teach bad behavior:
   table of contents, indexes, reference-book summaries, isolated headings,
   list scaffolding, repeated n-grams, and ultra-generic prose.
2. Rebuild v3.1 splits with hard gates:
   - every register in train/val/test;
   - at least two held-out authors per register where sources allow;
   - source lineage preserved;
   - author-disjoint splits.
3. Generate canonical `probes_balanced_n20.jsonl` with 5 probes per register
   and same-register swaps.
4. Regenerate content-focused instructions after filtering.
5. Only after CPU gates pass, launch a cheap short no-trunk warmstart smoke
   before any wider encoder or scale run.

## Decision Rule

Proceed to GPU smoke only if v3.1 passes the data gates in `config.yaml`.
Proceed beyond smoke only if:

- pathway remains non-collapsed (`balanced cos_K_last_swap <= 0.55`, random/code
  materially lower);
- final samples show less repetition than 010;
- the probe set includes poetry and speech.

## Results

v3.1 data gates pass.

| split | rows | essay | poetry | screenplay | speech |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 10,623 | 120 | 2,900 | 5,714 | 1,889 |
| val | 314 | 109 | 76 | 57 | 72 |
| test | 245 | 76 | 65 | 50 | 54 |

The filter removed 168 suspicious pairs:

- chapter-only headings: 58
- contents headings: 27
- index headings: 5
- repeated 5-grams: 78

The 1,500-step smoke completed. Final balanced n=20 pathway:

| metric | value |
| --- | ---: |
| `mean_cos_K_first_swap` | 0.482 |
| `mean_cos_K_last_swap` | 0.446 |
| `mean_cos_K_last_random` | 0.037 |
| `mean_cos_K_last_code` | 0.113 |

Per-register `cos_K_last_swap`:

- essay: 0.452
- poetry: 0.272
- screenplay: 0.256
- speech: 0.805

Qualitative result: not good enough for a full run. Screenplay improves and
looks structurally like screenplay. Poetry remains repetitive, essay can collapse
into repeated boilerplate, and speech emits `Transcript Transcript` plus public
document boilerplate.

Persisted artifacts:

- `results/v3_1_candidate/`
- `results/smoke_training/train_log.jsonl`
- `results/smoke_training/samples.jsonl`
- `results/v3_1_no_trunk_smoke_pathway_balanced_n20/`

## Learnings

See `LEARNINGS.md`.

## Replicate

Planned. Start from the repaired data builder and 010 artifacts:

```bash
cd text-ip-adapter
PYTHONPATH=src python scripts/build_v3_pairs.py --output-dir data/pairs_v3_1
```
