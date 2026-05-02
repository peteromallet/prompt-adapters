# Result readout: exp030 / v5.7 pair-audited stronger style

Status: completed. Train artifacts were intentionally skipped; eval artifacts and logs were
downloaded and the pod terminated cleanly.

## Change from exp029

Objective and hyperparameters stayed fixed:

- `style_triplet_weight`: 1.5
- `contrastive_weight`: 0.2
- `max_steps`: 1200

Only train data changed:

- exp029 train: v5.4, 3,859 pairs, 53 train authors
- exp030 train: v5.7 pair-audited min-25, 3,135 pairs, 47 train authors
- val/test/probes unchanged

## Pathway metrics

- `mean_cos_K_last_swap`: 0.1231
- `mean_cos_V_last_swap`: 0.1048
- `mean_cos_z_swap`: 0.4496
- `mean_gen_jaccard_swap`: 0.0790
- `mean_cos_K_last_random`: -0.0074
- `mean_cos_V_last_random`: -0.0013
- `mean_cos_K_last_code`: 0.0882
- `mean_cos_V_last_code`: 0.0404

Comparison:

- v5.0: `K_last_swap=0.1500`, `V_last_swap=0.1659`
- v5.4: `K_last_swap=0.2123`, `V_last_swap=0.1925`
- v5.5/exp029: `K_last_swap=0.1711`, `V_last_swap=0.1470`
- v5.7/exp030: `K_last_swap=0.1231`, `V_last_swap=0.1048`

This is the strongest pathway result so far. Pair-level auditing helped materially and did not
inflate random/code controls.

## Sampled qualitative read

Sampled eval wrote 48 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`, and
`prompted_baseline`.

- `adapter`: median 181.5 chars, no meta hits, max repeat-3 = 1.
- `adapter_swap`: median 245.5 chars, no broad meta hits by regex, max repeat-3 = 2.
- `no_ref`: median 436.5 chars, 3 meta/instruction hits, max repeat-3 = 2.
- `prompted_baseline`: median 410.5 chars, 2 meta/instruction hits, max repeat-3 = 1.

Qualitative verdict: mixed-positive. The adapter condition is cleaner and more poem-like than
baselines, and no-ref/baseline still leak obvious prompt/prose junk. However, adapter generations
remain generic and sometimes prose/dialogue-like rather than strongly author-specific. One
`adapter_swap` sample also produced question-answer prose about the sea, so surface generation is
not solved.

## Conclusion

The pair audit was worth doing. It produced the best conditioning/pathway result to date, and the
cleaned train split should become the current training-data baseline.

But the qualitative bottleneck remains: the model can route a reference-conditioned signal, yet
the decoded text is still not reliably high-style poetry. Next work should target generation-facing
alignment: prompt format, decoding, stronger author-style objective, or supervised style exemplars,
using v5.7 as the data baseline.
