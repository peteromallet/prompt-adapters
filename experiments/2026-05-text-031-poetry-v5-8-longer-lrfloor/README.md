# Experiment 031: v5.8 longer effective training with LR floor

## Question

Does the v5.7 pair-audited data still benefit from more optimization when the learning rate does not
collapse to near-zero during the final part of training?

## Why this is the next data/train-time balance test

Exp030 used the best current data baseline:

- train rows: 3,135
- train authors: 47
- objective: `style_triplet_weight=1.5`, `contrastive_weight=0.2`
- steps: 1,200

It produced the best pathway metrics so far:

- `mean_cos_K_last_swap=0.1231`
- `mean_cos_V_last_swap=0.1048`
- random/code controls stayed low

But the training schedule had effectively stopped learning by the end:

- step 1,000 projector LR: `7.28e-7`
- step 1,175 projector LR: `1.17e-8`

So plain continuation under the old cosine schedule is not a meaningful "more training" test. This
experiment keeps data and loss fixed, doubles the step budget, and adds `min_lr_ratio=0.10`.

## Config

`text-ip-adapter/configs/stage1_v5_8_poetry_pair_audited_min25_stronger_style_lrfloor_restart006.yaml`

Key changes from exp030:

- `max_steps`: 1200 -> 2400
- `min_lr_ratio`: 0.0 -> 0.10
- `save_every`: 400 -> 800

Everything else important stays fixed.

## Success criteria

Primary:

- pathway swap metrics stay at or below exp030 (`K<=0.123`, `V<=0.105`) without random/code control inflation

Secondary:

- sampled adapter generations become more consistently poem-like and less generic
- no increase in meta, Q/A, or prose leakage

## Interpretation

- If pathway and samples improve: train-time was a real bottleneck, but only with a non-dead LR schedule.
- If pathway improves and samples do not: generation-facing alignment is still the bottleneck.
- If pathway worsens or controls inflate: v5.7 is quality-limited or the stronger objective is already near its useful limit; return to data expansion/heldout prompt design rather than longer runs.
