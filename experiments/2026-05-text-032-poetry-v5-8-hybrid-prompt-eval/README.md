# Experiment 032: v5.8 hybrid prompt comparison

## Question

For the strongest current recipe, does the adapter add value when the base model also sees the
reference sample in the normal text prompt?

## Why this run exists

Exp031 skipped train-artifact download, so its final checkpoint is not available for eval-only
hybrid prompting. This run repeats the exp031 training recipe and uses the updated sampled eval that
adds:

- `prompted_baseline`: reference pasted into prompt, no adapter
- `adapter_prompted`: same pasted-reference prompt plus adapter prefix from the same reference

The key comparison is `adapter_prompted` vs `prompted_baseline`.

## Config

`text-ip-adapter/configs/stage1_v5_8_poetry_pair_audited_min25_stronger_style_lrfloor_restart006.yaml`

## Interpretation

- If `adapter_prompted` beats `prompted_baseline`, the adapter has a product-relevant use even if
  adapter-only generations remain imperfect.
- If it ties, the adapter is mostly redundant once the base LM can directly attend to the sample.
- If it loses, the prefix may interfere with ordinary in-context style prompting.

