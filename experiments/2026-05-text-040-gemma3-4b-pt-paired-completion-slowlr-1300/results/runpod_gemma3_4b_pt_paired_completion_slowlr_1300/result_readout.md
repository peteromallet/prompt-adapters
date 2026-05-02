# Result Readout

Exp040 completed and the pod was terminated.

## Setup

- Base: `google/gemma-3-4b-pt`
- Format: paired completion
- Data: `pairs_v5_10_poetry_llm_style_medium_strong`, 2868 train rows
- Steps: 1300
- LR: projector `5e-6`, encoder `2.5e-6`
- Style triplet: `1.0`
- Batch size: 1, so batch contrastive is still effectively inactive

## Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref |
|---|---:|---:|---:|
| step 800 | 0.500 / +0.027 | 0.583 / -0.015 | 0.417 / +0.016 |
| step 1000 | 0.250 / -0.087 | 0.500 / +0.106 | 0.417 / +0.051 |
| step 1200 | 0.500 / +0.019 | 0.250 / -0.028 | 0.083 / -0.109 |
| final 1300 | 0.583 / -0.021 | 0.500 / +0.007 | 0.250 / -0.006 |

Each cell is `win_rate / mean_delta`, `n=12`.

## Read

This did not beat exp039 step 1200. The slower LR/lower style-triplet recipe produces weaker and noisier adapter effects, and it never recovers the strong adapter-vs-no-ref result from exp039.

The next best bet is not more slow training. Keep paired completion, but restore real negative pressure. The most direct fix is a batch-size-independent negative loss: compare own reference embeddings against explicit swapped/random/code reference embeddings inside each sample, instead of relying on in-batch contrastive negatives that disappear at batch size 1.
