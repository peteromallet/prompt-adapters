# Distinctive style filter v1

Source train rows: 3135
Kept before min-author gate: 110
Final train rows: 55
Final train authors: 2

## Thresholds

{
  "min_chars": 220,
  "max_chars": 1800,
  "min_lines": 4,
  "min_doc_advantage": 0.015,
  "min_pair_cohesion": 0.035,
  "max_generic_per_100": 9.0,
  "min_pairs_per_author_after_filter": 20
}

## Main reject reasons

- `ref_doc_not_distinctive_medium`: 2805
- `target_doc_not_distinctive_medium`: 2804
- `too_short`: 1141
- `too_long`: 117
- `low_ref_target_cohesion`: 1

## Interpretation

This is intentionally stricter than artifact cleanup. It keeps rows whose chunk-level
character n-gram style is closer to same-author context than other-author context,
then keeps pairs whose reference and target are medium-length and not too far apart
stylometrically. It is a candidate training split, not a final proof of style quality.
