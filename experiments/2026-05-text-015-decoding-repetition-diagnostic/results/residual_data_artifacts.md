# Residual Data Artifacts After 015

015 shows decoding was the main cause of mechanical loops, but the samples also
exposed remaining corpus artifacts.

Quick scan of `data/pairs_v3_3_corrected_poetry_core3`:

| split | poetry rows | poetry stage/apparatus hits | screenplay rows | screenplay bare page-number hits |
| --- | ---: | ---: | ---: | ---: |
| train | 2,267 | 18 | 5,652 | 1,362 |
| val | 187 | 5 | 57 | 22 |
| test | 155 | 4 | 50 | 0 |

Interpretation:

- screenplay page-number artifacts are common enough to teach the model to emit
  stray `504.` / `278.` style lines;
- poetry still contains a small but visible amount of stage direction,
  table-of-contents, or prose apparatus text, which plausibly contributes to
  instruction/prose leakage;
- these are not large enough to explain 013's loop collapse, but they are
  large enough to block high-quality style claims.

Code follow-up:

- `build_v3_pairs.py` now flags bare screenplay page-number lines.
- `build_v3_pairs.py` now has additional poetry apparatus patterns for stage
  direction leaks found during the 015 audit.

These changes affect future rebuilds; the 015 run intentionally evaluated the
already-trained 013 checkpoint without changing data.
