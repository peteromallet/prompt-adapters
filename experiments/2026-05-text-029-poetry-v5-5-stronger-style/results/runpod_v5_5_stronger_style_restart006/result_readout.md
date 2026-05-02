# Result readout: exp029 / v5.5 stronger style pressure

Status: completed. Train artifacts were intentionally skipped; eval artifacts and logs were
downloaded and the pod terminated cleanly.

## Change from exp028

Data, split, architecture, LR, warm start, and step count stayed fixed. Only loss weights changed:

- `style_triplet_weight`: 0.7 -> 1.5
- `contrastive_weight`: 0.1 -> 0.2

## Pathway metrics

- `mean_cos_K_last_swap`: 0.1711
- `mean_cos_V_last_swap`: 0.1470
- `mean_cos_z_swap`: 0.4642
- `mean_gen_jaccard_swap`: 0.1519
- `mean_cos_K_last_random`: 0.0249
- `mean_cos_V_last_random`: 0.0358
- `mean_cos_K_last_code`: 0.1242
- `mean_cos_V_last_code`: 0.0661

Comparison:

- v5.0: `K_last_swap=0.1500`, `V_last_swap=0.1659`
- v5.2: `K_last_swap=0.2471`, `V_last_swap=0.2586`
- v5.4: `K_last_swap=0.2123`, `V_last_swap=0.1925`
- v5.5: `K_last_swap=0.1711`, `V_last_swap=0.1470`

This is the best clean-probe pathway result so far. Stronger style pressure improved v5.4
substantially without driving random/code similarity upward.

## Sampled qualitative read

Sampled eval wrote 48 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`, and
`prompted_baseline`.

- `adapter`: median 213 chars, no meta hits, max repeat-3 = 2.
- `adapter_swap`: median 207 chars, 2 meta hits, max repeat-3 = 2.
- `no_ref`: median 519.5 chars, 5 meta/instruction hits, max repeat-3 = 1.
- `prompted_baseline`: median 418 chars, 3 meta/instruction hits, max repeat-3 = 2.

Qualitative verdict is mixed. The main adapter condition remains poem-like and avoids the
instruction/meta junk. But outputs are still generic and often modern/plain rather than convincingly
author-specific. `adapter_swap` regressed slightly with two meta-style failures.

## Conclusion

The scientific direction is clearer now:

1. v13/v5.4 is the current corpus baseline.
2. Stronger style pressure is real and improves pathway metrics.
3. The remaining failure is not primarily duplicate data or obvious OCR artifacts; it is surface
   generation/style alignment.

Next best bet: keep the v5.4 corpus, keep stronger style pressure in the search space, and test
generation-facing changes: decoding/prompt format, style-negative sampling, or a more direct
author-style objective. Do not spend the next block only manually pruning more corpus rows.
