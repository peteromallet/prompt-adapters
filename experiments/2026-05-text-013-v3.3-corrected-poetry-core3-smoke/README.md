# Experiment 013 - v3.3 corrected-poetry core3 smoke

Status: completed

## Question

After fixing bogus Gutenberg poetry IDs and applying the audit-derived cleanup
from 012, does the no-trunk warmstart adapter produce better qualitative
generations on the three viable registers: poetry, screenplay, and speech?

## Why This Exists

The 012 audit changed the diagnosis. The data was not merely noisy; parts of
the poetry corpus were mislabeled at the source-list level. Examples:

- `amy_lowell:32100` was a German novel.
- `algernon_swinburne:35245` was a school geography/index book.
- `francis_thompson:29676` was modern prose.
- `rupert_brooke:3722` was a novel.
- `stephen_crane:37158` was a vivisection tract.
- `wallace_stevens:45209` was John Marston drama.
- several other expansion IDs pointed at non-poetry books.

Training another run on v3.2, or on the first GPT-mini-audited split, would
have been scientifically wrong. The first audited split also destroyed heldout
coverage for speech and poetry, so the audit had to be converted into source
fixes and deterministic filters before training.

## Method

1. Fix the Gutenberg poetry source list in `ingest_poetry.py`.
2. Rebuild poetry from corrected source IDs.
3. Reuse v3.2 screenplay/speech rows, then reapply:
   - transcript cleanup;
   - 012 high-confidence delete blocklist;
   - suspicious target/reference filters;
   - poetry apparatus filters for notes, indexes, title pages, catalog copy,
     biography snippets, and edition commentary.
4. Exclude essay for this smoke. After the audit deletes, essay has too few
   clean pairs to support meaningful train plus heldout.
5. Split with two held-out authors per register and author-disjoint train/val/test.
6. Run a 1,500-step smoke only if the CPU gates and spot checks pass.

## Data Gate Result

`data/pairs_v3_3_corrected_poetry_core3` passes gates.

| split | rows | poetry | screenplay | speech |
| --- | ---: | ---: | ---: | ---: |
| train | 8,908 | 2,267 | 5,652 | 989 |
| val | 294 | 187 | 57 | 50 |
| test | 255 | 155 | 50 | 50 |

All val/test registers have at least two held-out authors, and splits are
author-disjoint.

Targeted poetry contamination scan after filtering:

- bad marker count: 0
- checked for the known bad signatures from 012: school-reader catalog text,
  German novel prose, vivisection/serotherapy prose, geography index text,
  Tennyson annotation prose, line-note apparatus, and biography snippets.

Artifacts:

- `results/data_audit/manifest.json`
- `results/data_audit/spotcheck_samples.md`
- `results/data_audit/v3_2_gptmini_high_conf_delete_blocklist.json`

## Decision Rule

Launch only a smoke, not a full run.

Proceed beyond smoke only if:

- final `cos_K_last_swap` remains non-collapsed;
- random/code references remain materially lower than own/swap;
- poetry samples are recognizably poems and not title-page/notes prose;
- speech samples do not revive `Transcript`, `View Transcript`, or formal
  proclamation boilerplate;
- screenplay remains structurally sane.

## Run

```bash
cd text-ip-adapter
./scripts/launch_runpod_host.sh --config configs/stage1_v3_3_corrected_poetry_core3_smoke.yaml
```

If using an already-running pod, sync the repo/data and run:

```bash
cd /workspace/text-ip-adapter
PYTHONPATH=src python scripts/train.py --config configs/stage1_v3_3_corrected_poetry_core3_smoke.yaml
```

## Results

The 1,500-step smoke completed on RunPod pod `5fb510b915pz3n`. The pod was
terminated after artifacts were downloaded.

Persisted artifacts:

- `results/smoke_training/train_log.jsonl`
- `results/smoke_training/samples.jsonl`
- `results/v3_3_corrected_poetry_core3_pathway_balanced_n15/analysis.json`
- `results/v3_3_corrected_poetry_core3_pathway_balanced_n15/generations.jsonl`

Pathway summary:

| metric | value |
| --- | ---: |
| `mean_cos_z_swap` | 0.409 |
| `mean_cos_K_first_swap` | 0.469 |
| `mean_cos_K_last_swap` | 0.398 |
| `mean_cos_K_last_random` | -0.039 |
| `mean_cos_K_last_code` | 0.044 |
| `mean_gen_jaccard_swap` | 0.036 |

Qualitative result: failed. Poetry is no longer corrupted by bogus source
books, and screenplay/speech have the right register shape, but all three still
repeat phrases or sentences. This points away from global pathway collapse and
toward objective/decoding/training dynamics.

Decision: do not run full v3.3. Next best bet is a cheap ablation on the same
data with `contrastive_weight=0` and a smaller smoke probe set.
