# Experiment 030: v5.7 pair-audited training data

Purpose: test whether manual/subagent pair-level cleanup improves the stronger-style direction.

## Inputs

- Pair set: `text-ip-adapter/data/pairs_v5_7_poetry_pair_audited_min25`
- Config: `text-ip-adapter/configs/stage1_v5_7_poetry_pair_audited_min25_stronger_style_restart006.yaml`
- Warm start: `checkpoints/stage1_gemma_no_trunk/final.pt` on the RunPod network volume

## Change from exp029

Objective and hyperparameters stay fixed:

- `style_triplet_weight`: 1.5
- `contrastive_weight`: 0.2
- `max_steps`: 1200

Data changes:

- Train rows: 3,859 -> 3,135
- Train authors: 53 -> 47
- Removed 685 audited bad pairs plus 39 low-count author pairs after audit.
- Val/test/probes unchanged from v5.4/v5.5.

Success signal: pathway matches or beats exp029 and sampled adapter output becomes less generic or
less contaminated. If pathway worsens, the cleanup may have removed useful diversity or the model
needs more data after all.
