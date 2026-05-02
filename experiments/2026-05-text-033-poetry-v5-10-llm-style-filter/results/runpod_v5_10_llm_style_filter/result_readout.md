# Result readout: exp033 / v5.10 LLM style-filtered pairs

Status: completed. The pod terminated cleanly and train/eval artifacts were downloaded.

## Change from exp032

Training recipe stayed fixed:

- restart from `checkpoints/stage1_gemma_no_trunk/final.pt`
- `max_steps=2400`
- `min_lr_ratio=0.10`
- `style_triplet_weight=1.5`
- `contrastive_weight=0.2`

Only train data changed:

- exp032/v5.7 train: 3,135 pairs, 47 authors
- exp033/v5.10 train: 2,868 pairs, 44 authors
- v5.10 came from LLM style audit v2:
  - `keep`: 2,668
  - `edit`: 200
  - `delete`: 267

## Pathway metrics

- `mean_cos_K_last_swap`: 0.0946
- `mean_cos_V_last_swap`: 0.1078
- `mean_cos_z_swap`: 0.4184
- `mean_gen_jaccard_swap`: 0.0771
- `mean_cos_K_last_random`: -0.0116
- `mean_cos_V_last_random`: 0.0069
- `mean_cos_K_last_code`: 0.0730
- `mean_cos_V_last_code`: 0.0541

Comparison:

- exp031/v5.8: `K_last_swap=0.0504`, `V_last_swap=0.0446`
- exp032/v5.8 rerun: `K_last_swap=0.0541`, `V_last_swap=0.0471`
- exp033/v5.10: `K_last_swap=0.0946`, `V_last_swap=0.1078`

The pathway remains separated but regressed relative to exp031/032. Random/code controls are still
low enough that this is not global collapse.

## Sampled qualitative read

Sampled eval wrote 60 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`,
`prompted_baseline`, and `adapter_prompted`.

- `adapter`: median 180.5 chars, meta hits 0, prose hits 0, max repeat-3 = 1.
- `adapter_prompted`: median 169 chars, meta hits 0, prose hits 0, max repeat-3 = 1.
- `prompted_baseline`: median 330 chars, meta hits 1, prose hits 1, max repeat-3 = 1.
- `no_ref`: median 484 chars, meta hits 1, prose hits 0, max repeat-3 = 2.
- `adapter_swap`: median 170.5 chars, meta hits 0, prose hits 0, max repeat-3 = 1.

Surface cleanliness improved versus exp032: no broad meta/prose hits in adapter or
adapter_prompted by the simple regex pass.

But qualitative style adherence is still not solved. The adapter still has task-format failures:

- Dickinson adapter: "What do they mean by..." rather than a poem.
- Stephen Crane adapter includes "This is what I wrote but it's not very good."
- Newman adapter asks a question about articles.
- Some adapter_prompted outputs are good local imitations, but others remain prose/paraphrase or
  short abrupt fragments.

## Finding

The LLM style filter helped surface cleanliness but did not produce a decisive style-adherence
breakthrough. It also weakened the best pathway metric compared with v5.8.

The main lesson is that pair filtering alone is not enough. We likely need:

1. Better eval probes with clean, distinctive heldout references and expected targets.
2. A pairwise style-adherence judge comparing output A/B against the reference.
3. A stronger generation-facing objective or prompt format, because K/V separation still does not
   reliably become author-style adherence.

## Next steps

Do not simply train longer on v5.10.

Recommended next work:

1. Build a dedicated style-adherence eval set from the LLM-audited medium/strong data, not the old
   v5.0 probes.
2. Add a judge/evaluator for `adapter` vs `no_ref`, `adapter_prompted` vs `prompted_baseline`, and
   `adapter` vs `adapter_swap`.
3. Inspect v5.10 deletions/keeps for audit consistency; several shards had very different delete
   rates, so calibration may be uneven.
4. If retraining, try a hybrid/product-format objective only after the eval set can measure whether
   the adapter actually improves style adherence.

