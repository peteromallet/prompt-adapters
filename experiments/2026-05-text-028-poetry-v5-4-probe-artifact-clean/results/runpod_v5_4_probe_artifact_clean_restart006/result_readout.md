# Result readout: exp028 / v5.4 probe-artifact-clean restart006

Status: completed. Train artifacts were intentionally not downloaded to avoid the exp027 disk
failure; eval artifacts and logs were downloaded and the pod terminated cleanly.

## Pathway metrics

- `mean_cos_K_last_swap`: 0.2123
- `mean_cos_V_last_swap`: 0.1925
- `mean_cos_z_swap`: 0.5245
- `mean_gen_jaccard_swap`: 0.1127
- `mean_cos_K_last_random`: 0.0266
- `mean_cos_K_last_code`: 0.1524

Comparison:

- v5.0: `K_last_swap=0.1500`, `V_last_swap=0.1659`
- v5.2: `K_last_swap=0.2471`, `V_last_swap=0.2586`
- v5.4: `K_last_swap=0.2123`, `V_last_swap=0.1925`

v5.4 recovers part of the v5.2 regression, especially on V, but does not beat v5.0. Since
v5.4's probes are cleaner than v5.0's, the strict numeric comparison is not perfectly apples to
apples; still, the result does not support "data cleanup alone solves it."

## Sampled qualitative read

Sampled eval wrote 48 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`, and
`prompted_baseline`.

- `adapter`: median 190.5 chars, no meta hits, max repeat-3 = 2.
- `adapter_swap`: median 232.5 chars, no meta hits, max repeat-3 = 1.
- `no_ref`: median 433 chars, 5 meta/instruction hits, max repeat-3 = 2.
- `prompted_baseline`: median 365.5 chars, 1 meta/instruction hit, max repeat-3 = 1.

The adapter is clearly doing something useful: it suppresses the no-ref/baseline instruction
and prose-template behavior. But the adapter generations are still too generic, sometimes
prose-like, and weakly tied to the reference author's style.

## Conclusion

The v13/v5.4 corpus is the best cleaned corpus so far, and it is good enough to continue using.
But the experiment says the next bottleneck is probably objective pressure/style-axis alignment,
not another round of broad manual corpus cleaning.

Next best experiment: keep v5.4 data fixed and increase style-discrimination pressure, so the
only changed variable is the loss balance.
