# Result Readout

Exp041 completed. The runner hit local disk full while downloading train artifacts, but eval artifacts and logs are local. I freed generated checkpoint/tar artifacts and confirmed the pod is no longer present on the RunPod account.

## Setup

- Base: `google/gemma-3-4b-pt`
- Format: paired completion
- Steps: 1300
- LR: projector `1e-5`, encoder `5e-6`
- Style triplet: `1.5`
- New loss: `style_contrastive_weight=0.5`, `temperature=0.2`

## Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref |
|---|---:|---:|---:|
| step 800 | 0.417 / +0.016 | 0.500 / -0.014 | 0.667 / +0.026 |
| step 1000 | 0.417 / +0.015 | 0.333 / -0.054 | 0.417 / -0.054 |
| step 1200 | 0.417 / +0.007 | 0.333 / +0.011 | 0.167 / -0.045 |
| final 1300 | 0.250 / -0.026 | 0.417 / -0.030 | 0.417 / -0.080 |

Each cell is `win_rate / mean_delta`, `n=12`.

## Read

The explicit negative loss is mechanically working: pathway swap similarity drops a lot. But generated text judgments do not improve. This is not the next winning direction at this weight.

Best current checkpoint remains exp039 step 1200. Next best scientific move is not more brute-force training; it is either much subtler style loss, reduced adapter intervention strength, or a larger pairwise eval to reduce noise before optimizing against these small deltas.
