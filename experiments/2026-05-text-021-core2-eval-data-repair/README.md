# Experiment 021 - Core2 Eval/Data Repair

Status: completed.

## Question

Was 020's weak poetry result partly an eval/data artifact, and which checkpoint
is best after repairing the core2 probe/data issues?

## Why This Exists

020 passed the aggregate core2 pathway gate, but the split showed screenplay
carrying the result while poetry stayed weak. During follow-up audit, v3.6 also
showed two concrete problems:

- training screenplay still had timecode/page/revision artifacts;
- balanced n20 probes repeated the same poetry reference documents, especially
  the Hardy→Teasdale pair.

021 repairs those issues before another training spend.

## Method

- Dataset: `data/pairs_v3_7_core2_repaired`.
- Config: `configs/stage1_v3_7_core2_repaired_eval.yaml`.
- Eval checkpoints:
  - `018_step1000`: `checkpoints/stage1_v3_5_artifact_clean_core3_longer/step_1000.pt`
  - `020_final`: `checkpoints/stage1_v3_6_core2_poetry_screenplay_smoke/final.pt`
- Run pathway on repaired balanced n20 probes.
- Run sampled anti-repeat eval on the same repaired probes.

## Decision Rule

If repaired probes make poetry much healthier without retraining, the prior
poetry weakness was partly an eval artifact. If `020_final` beats
`018_step1000`, keep core2 continuation. If both remain poetry-weak, next move
is a poetry-focused negative-pair/data ablation, not wider encoder.

## Result

`020_final` remains the best current checkpoint on repaired core2 probes:

- `020_final`: `cos_K_last_swap=0.502`, random=-0.071, code=-0.091.
- `018_step1000`: `cos_K_last_swap=0.598`, random=-0.091, code=-0.098.

The repaired probe changed the register diagnosis:

- poetry is better than 020's v3.6 probe suggested (`0.522` vs `0.633`);
- screenplay is less trivially strong once refs diversify (`0.483` vs `0.248`).

Both checkpoints stay clean on T4 and repetition. Surface T3 is still weak, so
this is not a C1 claim win. See `results/analysis_summary.md`.
