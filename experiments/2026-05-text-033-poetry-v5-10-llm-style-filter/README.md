# Experiment 033: v5.10 LLM style-filtered poetry pairs

## Question

Does filtering train pairs to clean medium/strong distinctive writing style improve decoded style
adherence while preserving the strong v5.8 pathway?

## Data

Source: `pairs_v5_7_poetry_pair_audited_min25`

LLM style audit v2:

- source train rows: 3,135
- delete: 267
- edit: 200
- keep: 2,668
- final train rows: 2,868
- final train authors: 44

Output: `text-ip-adapter/data/pairs_v5_10_poetry_llm_style_medium_strong`

## Training

Same recipe as exp031/032:

- restart from `checkpoints/stage1_gemma_no_trunk/final.pt`
- `max_steps=2400`
- `min_lr_ratio=0.10`
- `style_triplet_weight=1.5`
- `contrastive_weight=0.2`

## Success Criteria

- pathway remains healthy, ideally close to exp031/032 (`K_last_swap ~= 0.05`)
- adapter samples have fewer generic/prose/meta failures
- `adapter_prompted` no longer harms the visible-reference prompt baseline

