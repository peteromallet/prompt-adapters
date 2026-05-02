# 025 Analysis Summary

Status: completed, pathway-positive, surface-mixed.

## Runs

- First run: `runpod_poetry_strict_restart006`
  - Pod `6h88m2oeyt2xd3`
  - Training and eval completed, but local artifact download failed on the
    2.7GB train archive (`No space left on device`). Pod terminated cleanly.
  - Remote pathway summary was captured in logs.
- Repeat run: `runpod_poetry_strict_restart006_repeat`
  - Pod `zbt9ajtofk0xo5`
  - Completed cleanly and terminated.
  - Eval artifacts and final checkpoint downloaded after patching the launcher
    to download eval first, prune `step_*.pt`, and remove local tar archives.

## Pathway Result

Repeat run strict-poetry pathway:

- `mean_cos_K_last_swap = 0.4053`
- `mean_cos_V_last_swap = 0.3854`
- `mean_cos_K_last_random = 0.1012`
- `mean_cos_K_last_code = 0.1387`
- `mean_gen_jaccard_swap = 0.0035`

Baseline from 024c poetry:

- `cos_K_last_swap = 0.5592`

Interpretation: strict poetry-only training substantially improved the poetry
style pathway, nearly hitting the target gate (`<=0.40`) and preserving
random/code separation. This validates poetry-specific data/objective repair as
a useful direction.

## Sampled Output Read

Sampled anti-repeat eval produced 64 rows:

- adapter rows: 16
- adapter swap rows: 16
- no-ref rows: 16
- prompted baseline rows: 16

Simple adapter metrics:

- `repeat3_mean = 0.0050`
- `repeat3_max = 0.0500`
- `line_repeat_mean = 0.0`
- own-vs-swap generation 3-gram Jaccard mean/max: `0.0 / 0.0`

Qualitative read: not solved. Many adapter outputs are verse-like and low
repeat, but several still show instruction/meta leakage or prose/essay drift:

- `edna_millay_01`: starts with instruction-like prose.
- `emily_dickinson_01`: "You must use all of the following lines..."
- `sara_teasdale_00`: "If you were to try and write that..."
- `stephen_crane_00`: essay-like "The Refutation" prose.

## Conclusion

025 is a real positive update for the pathway hypothesis, but not a C1/style
claim win. The best next move is not another broad data-cleaning pass. Either:

1. add a stronger style-supervision objective, such as author/prototype or hard
   batch-negative style loss, or
2. add a surface-quality constraint/eval that penalizes instruction/meta/prose
   leakage during model selection.

The result is strong enough to continue from this direction, but the remaining
blocker is output alignment, not K/V signal propagation.

## v4.5 Structural-Balanced Follow-Up

After manual cleanup, v4.4 still had structural duplication: repeated
references, duplicate targets, and a 15-row probe set after deleting a bad
Masefield probe. v4.5 fixed this by keeping the manual edits/deletes, deduping
exact target text, capping repeated references, and rebuilding 16 balanced
probes.

Dataset:

- `pairs_v4_5_poetry_structural_balanced`
- train: 727 rows, 31 unique refs, max ref repeat 40, zero target duplicate
  groups
- val: 183 rows, 7 unique refs, max ref repeat 30, zero target duplicate groups
- test: 134 rows, 6 unique refs, max ref repeat 30, zero target duplicate groups
- probes: 16 rows, 8 heldout authors, 2 per author

Run:

- `runpod_poetry_v45_structural_balanced_restart006`
- Pod `e4sjagd00oa5kl`
- Training and eval completed, pod terminated.
- Local train checkpoint download failed because the Mac had ~1GB free disk,
  but eval artifacts downloaded successfully before the failure.

Pathway:

- `mean_cos_K_last_swap = 0.4340`
- `mean_cos_V_last_swap = 0.4025`
- `mean_cos_K_last_random = -0.0650`
- `mean_cos_K_last_code = 0.0173`
- `mean_gen_jaccard_swap = 0.0067`

Interpretation: v4.5 is worse than the v4.3 repeat (`0.4053`) but still much
better than 024c poetry (`0.5592`). Removing structural duplication did not
kill the pathway, but v4.3 probably benefited modestly from repeated-reference
exposure.

Surface read:

- 64 sampled rows were produced.
- Adapter rows: repeat3 max 1, crude explicit meta regex hits 0/16.
- Adapter-swap rows: repeat3 max 1, crude explicit meta regex hits 1/16.
- This is cleaner by simple regex than v4.3, but still not solved: some adapter
  outputs are prose-like or contain placeholders/quote drift, e.g.
  `edna_millay_01` and `edwin_arlington_robinson_00`.

Updated conclusion: easy structural cleanup helped the evaluation hygiene and
did not destroy the style pathway. The next bottleneck is not duplicate cleanup;
it is either data coverage for genuinely thin authors or a stronger
surface/style objective that penalizes prose, classroom prompts, placeholders,
and non-poem completions.
