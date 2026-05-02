# Experiment 014 Analysis Summary

Status: completed on 2026-04-25.

## Result

The no-contrastive ablation is **refuted**.

It did not fix the repeated generations seen in 013, and it degraded reference
pathway separation.

## Pathway

Post-training n=6 pathway:

| metric | value |
| --- | ---: |
| `mean_cos_z_swap` | 0.720 |
| `mean_cos_K_first_swap` | 0.861 |
| `mean_cos_K_last_swap` | 0.792 |
| `mean_cos_K_last_random` | 0.126 |
| `mean_cos_K_last_code` | 0.201 |
| `mean_gen_jaccard_swap` | 0.075 |

013, by contrast, had `mean_cos_K_last_swap=0.398`, random=-0.039, and
code=0.044. Removing contrastive pushed own/swap K/V back toward collapse.

## Qualitative

Final samples remain unacceptable:

- poetry repeats short phrase structures such as "When the dust is thick" and
  "Happy is a state of mind";
- screenplay is often formatted correctly but repeats scene-local beats;
- speech sometimes improves in surface form, but still repeats stock openings or
  clauses;
- no-ref remains generic and repetitive.

## Decision

Keep contrastive on. It remains a useful anti-collapse term.

The next experiment should not be another corpus-only cleanup or a
contrastive-off run. The fastest decisive test is a decoding-control diagnostic
on the 013 checkpoint: same corrected v3.3 core3 data, same trained checkpoint,
but generate with explicit repetition controls. If that cleans up samples, the
near-term fix is generation/eval decoding alignment. If it does not, the next
training run should change the supervised target/objective directly.
