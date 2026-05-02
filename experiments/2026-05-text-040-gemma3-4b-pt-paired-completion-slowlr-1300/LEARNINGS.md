# 2026-05-text-040-gemma3-4b-pt-paired-completion-slowlr-1300

## Result

This was a negative follow-up to exp039.

Exp039 showed a clear but narrow peak at step 1200 with paired completion:

- adapter vs swap: `0.583 / +0.043`
- adapter vs no-ref: `0.667 / +0.142`

Exp040 tested whether a gentler schedule could preserve that effect:

- LR halved: projector `5e-6`, encoder `2.5e-6`
- style triplet reduced: `1.5 -> 1.0`
- max steps reduced: `2000 -> 1300`
- checkpoint evals at 800, 1000, 1200, final

It did not work.

## Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref | read |
|---|---:|---:|---:|---|
| step 800 | 0.500 / +0.027 | 0.583 / -0.015 | 0.417 / +0.016 | mild swap signal, weak no-ref |
| step 1000 | 0.250 / -0.087 | 0.500 / +0.106 | 0.417 / +0.051 | some swap delta, prompt path worse |
| step 1200 | 0.500 / +0.019 | 0.250 / -0.028 | 0.083 / -0.109 | collapse |
| final 1300 | 0.583 / -0.021 | 0.500 / +0.007 | 0.250 / -0.006 | weak/noisy |

Each cell is `win_rate / mean_delta`, `n=12`.

## Interpretation

Lower LR and lower style-triplet did not solve the exp039 overtraining problem. It appears to make the adapter too weak or misbalanced. The good exp039 checkpoint was not reproduced by simply slowing the recipe down.

The important unresolved issue remains batch size 1. With the paired-completion prompt, VRAM forced batch 1, which makes generic batch contrastive zero. We are relying on style triplet alone for discrimination, and the result is unstable.

## Next Bet

Do not keep pushing the slow-LR branch.

Return to exp039's stronger LR/loss scale and fix negative pressure:

1. Keep paired completion.
2. Restore effective contrastive negatives even at batch size 1, or shorten prompts enough for batch > 1.
3. Evaluate around 1000-1300 steps.
4. Treat exp039 `step_1200` as the current best checkpoint.

Most likely next implementation: add an explicit within-sample negative loss where the same target/reference batch compares own reference embeddings against swapped/random/code references, independent of batch size.
