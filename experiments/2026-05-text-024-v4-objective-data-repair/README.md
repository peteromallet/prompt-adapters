# 2026-05-text-024-v4-objective-data-repair

Status: 024a completed; 024b running.

## Question

Does a direct within-register author-style triplet objective repair the gap exposed by 023, where generic K/V decorrelation separated references but did not reliably align the pathway with author style?

## 024a: Triplet On v3.9

Continue the 022 checkpoint for 500 steps on `pairs_v3_9_core2_evalclean`:

- init: 022 final checkpoint
- data: v3.9 clean-eval core2 dataset
- generic contrastive weight: `0.02`
- style triplet weight: `0.25`
- triplet: anchor ref vs same-author positive ref vs same-register different-author negative ref
- eval: v3.9 balanced pathway and sampled anti-repeat generations

This is a cheap diagnostic, not a final claim run.

Result: negative/informative. The direct triplet objective helped poetry a
little but did not materially solve same-register author binding.

## 024b: v4 Style-Clean Data

Staged follow-up: continue the same 022 checkpoint on
`pairs_v4_core2_styleclean`, which normalizes instructions to generic
register-level style requests and strips remaining source artifacts from
train/val/test. This tests whether the old v3.9 training distribution, not just
the objective, was holding the style axis in the wrong place.
