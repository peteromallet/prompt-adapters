# Experiment 014 - objective ablation core3

Status: completed on 2026-04-25.

## Question

Does disabling contrastive K/V decorrelation reduce the repetitive generations
seen in 013 on the corrected v3.3 core3 corpus?

## Hypothesis

013 fixed major data corruption and kept the pathway healthy, but samples still
looped. The immediate suspect is now objective/training dynamics. Contrastive
loss may preserve K/V diversity while competing with next-token style learning.

If `contrastive_weight=0` improves repetition while pathway remains acceptable,
the next objective should separate style learning from K/V decorrelation more
carefully. If it still repeats, the problem is deeper than contrastive
competition.

## Method

- Same dataset as 013: `data/pairs_v3_3_corrected_poetry_core3`.
- Same no-trunk warmstart checkpoint.
- Disable contrastive: `contrastive_weight=0.0`.
- Shorten to 750 steps.
- Use a 6-probe balanced smoke set, two probes per register, to reduce sampling
  latency.

## Config

`text-ip-adapter/configs/stage1_v3_3_core3_no_contrastive_smoke.yaml`

## Decision Rule

Compare against 013:

- repetition should visibly improve in final samples;
- no-ref should remain a negative control;
- pathway probe should not collapse to swap/random/code similarity near 1.0.

This is not a full claim-supporting run. It is a diagnostic ablation.

## Result

The hypothesis is refuted.

Disabling contrastive did not remove the visible repetition. Final samples still
loop across all three registers: poetry repeats short lines and phrases,
screenplay repeats scene beats, and speech repeats stock clauses.

It also made the reference pathway worse than 013:

| metric | 013 contrastive-on | 014 contrastive-off |
| --- | ---: | ---: |
| `mean_cos_z_swap` | 0.409 | 0.720 |
| `mean_cos_K_first_swap` | 0.469 | 0.861 |
| `mean_cos_K_last_swap` | 0.398 | 0.792 |
| `mean_cos_K_last_random` | -0.039 | 0.126 |
| `mean_cos_K_last_code` | 0.044 | 0.201 |

The no-contrastive run is therefore worse on the pathway and not materially
better on qualitative generation. Contrastive remains necessary for reference
separation; the repetition problem is elsewhere.

## Decision

Do not continue with contrastive-off training and do not full-run this branch.

Next best bet: hold the 013 checkpoint/data fixed and test direct
anti-repetition generation controls first. If decoding controls clean up the
outputs without changing pathway metrics, training/eval decoding is the
immediate lever. If deterministic decoding still loops under repetition
controls, move to a training objective change such as target window shaping or
unlikelihood-style anti-repetition loss.
