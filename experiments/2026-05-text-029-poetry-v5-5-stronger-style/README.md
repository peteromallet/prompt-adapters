# Experiment 029: v5.5 stronger style pressure

Purpose: test whether v5.4's remaining weakness is loss balance rather than corpus contamination.

## Inputs

- Pair set: `text-ip-adapter/data/pairs_v5_4_poetry_corpus_probe_artifact_clean`
- Config: `text-ip-adapter/configs/stage1_v5_5_poetry_corpus_probe_clean_stronger_style_restart006.yaml`
- Warm start: `checkpoints/stage1_gemma_no_trunk/final.pt` on the RunPod network volume

## Change from exp028

Data, split, architecture, learning rates, and step count stay fixed. Only objective weights change:

- `style_triplet_weight`: 0.7 -> 1.5
- `contrastive_weight`: 0.1 -> 0.2

Hypothesis: exp028 showed clean adapter generations but weak author-style specificity. If the
style signal is underweighted relative to next-token loss, stronger style pressure should improve
pathway separation and ideally make sampled adapter output less generic without reintroducing
collapse.

Success signal:

- `mean_cos_K_last_swap` and `mean_cos_V_last_swap` improve over exp028 without random/code
  similarities rising toward swap.
- Sampled `adapter` and `adapter_swap` remain poem-like and become more reference-sensitive.
