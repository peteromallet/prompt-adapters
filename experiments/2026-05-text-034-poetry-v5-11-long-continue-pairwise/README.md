# Experiment 034: v5.10 long continuation with checkpoint pairwise eval

## Question

Does substantially more training from the exp033 final checkpoint improve decoded style adherence,
and where does it peak?

## Setup

- Data: `pairs_v5_10_poetry_llm_style_medium_strong`
- Init: exp033 final checkpoint uploaded to `/tmp/exp033_final.pt`
- Additional steps: 3,600
- LR: half exp033 (`5e-6` projector, `2.5e-6` encoder), LR floor `0.10`
- Checkpoints: step 1000, 2000, 3000, final
- Eval per checkpoint:
  - pathway diagnostics
  - sampled generations
  - deterministic pairwise style/prompt-adherence eval

## Decision

Prefer the checkpoint with the best combination of:

- clean generated samples
- `adapter` beats `no_ref`
- `adapter_prompted` beats or at least does not harm `prompted_baseline`
- pathway controls remain separated

