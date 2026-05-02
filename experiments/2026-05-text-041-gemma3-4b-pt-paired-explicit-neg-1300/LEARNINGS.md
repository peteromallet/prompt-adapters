# 2026-05-text-041-gemma3-4b-pt-paired-explicit-neg-1300

## Result

This was a useful negative result.

We added an explicit batch-size-independent style contrastive loss:

```text
softplus((sim(anchor, negative) - sim(anchor, positive)) / temperature)
```

over projected K/V tensors. This was meant to fix the paired-completion batch-size-1 problem: the old generic contrastive loss is zero at `B=1`, and margin triplet can stop exerting pressure once the margin is satisfied.

The new loss was active during training and did change representation geometry. In pathway eval, swap similarity dropped hard by step 1200:

- exp039 step 1200: K/V swap `0.246 / 0.395`
- exp041 step 1200: K/V swap `0.022 / 0.302`

But generation judgments did not improve.

## Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref | read |
|---|---:|---:|---:|---|
| step 800 | 0.417 / +0.016 | 0.500 / -0.014 | 0.667 / +0.026 | no-ref win returns, swap neutral |
| step 1000 | 0.417 / +0.015 | 0.333 / -0.054 | 0.417 / -0.054 | regresses |
| step 1200 | 0.417 / +0.007 | 0.333 / +0.011 | 0.167 / -0.045 | poor despite pathway separation |
| final 1300 | 0.250 / -0.026 | 0.417 / -0.030 | 0.417 / -0.080 | weak |

Each cell is `win_rate / mean_delta`, `n=12`.

## Interpretation

The bottleneck is not just "K/V vectors are insufficiently separated." Exp041 separated them more cleanly, but that separation did not translate into better style adherence in generated text.

That suggests the style vector space and the generation objective are only loosely aligned. Exp039's step-1200 result may be a narrow beneficial balance where the adapter nudges continuation style without overpowering or moving into a representation direction that judges do not reward.

## Current Best

Exp039 step 1200 remains the best checkpoint:

- adapter vs swap: `0.583 / +0.043`
- adapter vs no-ref: `0.667 / +0.142`

## Next Bet

Do not increase explicit contrastive strength. The next useful experiments should change one of:

1. Lower explicit style contrastive weight dramatically, e.g. `0.05-0.1`, if keeping it.
2. Reduce adapter intervention strength or injection span so the hidden vector nudges rather than dominates.
3. Improve eval reliability: `n=12` is too small for noisy pairwise conclusions.
4. Continue data work toward more distinctive, same-author-coherent pairs.

The highest-confidence conclusion is still: paired completion is the right framing for the PT model; loss geometry needs subtler alignment than blunt K/V separation.
