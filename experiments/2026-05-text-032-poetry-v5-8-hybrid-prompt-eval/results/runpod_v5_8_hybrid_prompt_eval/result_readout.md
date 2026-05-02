# Result readout: exp032 / v5.8 hybrid prompt eval

Status: completed. The pod terminated cleanly and the final checkpoint was downloaded locally:

`train_artifacts/tmp/stage1_v5_8_hybrid_prompt_eval/final.pt`

## Question

Does the adapter improve normal in-context style prompting when the reference sample is also visible
in the text prompt?

Key comparison:

- `prompted_baseline`: base model sees reference in prompt, no adapter.
- `adapter_prompted`: same visible-reference prompt plus adapter prefix from the same reference.

## Pathway metrics

The rerun reproduced exp031's strong pathway result:

- `mean_cos_K_last_swap`: 0.0541
- `mean_cos_V_last_swap`: 0.0471
- `mean_cos_z_swap`: 0.3888
- `mean_cos_K_last_random`: -0.0794
- `mean_cos_V_last_random`: -0.0694
- `mean_cos_K_last_code`: 0.0271
- `mean_cos_V_last_code`: -0.0219

So the adapter mechanism is still healthy. The hybrid result is not explained by pathway collapse.

## Sampled eval summary

Sampled eval wrote 60 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`,
`prompted_baseline`, and `adapter_prompted`.

- `adapter`: median 191 chars, meta hits 1, max repeat-3 = 2.
- `adapter_prompted`: median 153.5 chars, meta hits 1, max repeat-3 = 1.
- `prompted_baseline`: median 501.5 chars, meta hits 1, max repeat-3 = 2.
- `no_ref`: median 507 chars, meta hits 3, max repeat-3 = 1.
- `adapter_swap`: median 194.5 chars, meta hits 0, max repeat-3 = 1.

## Qualitative verdict

`adapter_prompted` did not beat `prompted_baseline`.

The visible-reference prompt often produced flawed but more complete style attempts. The
adapter+prompt condition tended to shorten, derail, or make the output abrupt. Examples:

- Cushag: `prompted_baseline` attempted dialectal domestic verse; `adapter_prompted` only wrote
  "What do you want to tell us ?"
- Emily Dickinson: `prompted_baseline` was poor, but `adapter_prompted` became explanatory prose
  about an elegy.
- Stephen Crane: `adapter_prompted` wrote "There is no response for this exercise yet."
- Buchanan: `prompted_baseline` stayed in lineated poem form; `adapter_prompted` paraphrased the
  reference as prose.

There were occasional decent hybrid outputs, but not enough to call the adapter useful as a
prompting enhancer.

## Finding

The adapter is good at routing a reference-conditioned signal, but we still do not have strong
evidence of decoded author-style adherence.

Exp032 refutes the optimistic product hypothesis that the current adapter simply improves normal
reference-in-prompt generation. The next best bet is data/objective work, not more training time
on the same data:

1. Filter training pairs to clean medium/strong distinctive writing style.
2. Remove weak generic poetry even if it is technically clean.
3. Build eval around pairwise style adherence, not just pathway cosines.
4. Retrain using the exp031/032 LR-floor recipe on the stricter corpus.

