# Experiment 028: v5.4 probe-artifact-clean poetry corpus

Purpose: isolate the effect of the v13/v5.4 corpus repair while keeping the exp027 training
objective and hyperparameters fixed.

## Inputs

- Corpus: `text-ip-adapter/data/poetry_corpus_v0_source_native_curated_candidate_v13`
- Pair set: `text-ip-adapter/data/pairs_v5_4_poetry_corpus_probe_artifact_clean`
- Config: `text-ip-adapter/configs/stage1_v5_4_poetry_corpus_probe_artifact_clean_triplet_restart006.yaml`
- Warm start: `checkpoints/stage1_gemma_no_trunk/final.pt` on the RunPod network volume

## Corpus summary

- Rows: 18,664
- Authors: 65
- Sources: 79
- Deterministic audit: pass, duplicate clean hashes: 0
- Pair rows: train 3,859 / val 144 / test 144
- Probe rows: 12 heldout author probes

## Why this run

Exp027/v5.2 completed but showed two facts at once:

1. The adapter is still helping relative to no-ref/baseline generations.
2. The corpus still leaked table-of-contents, preface, publisher/review, and commentary rows.

v5.4 is the shortest clean scientific step: same model, same objective, same training length,
cleaner data. If pathway improves back toward or past v5.0 while qualitative samples stay clean,
the data-cleaning direction is confirmed. If not, the next bottleneck is likely objective/decoding
rather than gross corpus contamination.
