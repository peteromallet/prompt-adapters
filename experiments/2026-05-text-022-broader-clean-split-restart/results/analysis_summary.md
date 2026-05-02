# Experiment 022 Analysis Summary

Status: completed with manual orchestration recovery.

## Artifacts

- Run manifest: `results/runpod_tmp/launch_manifest.json`
- Train artifacts: `results/runpod_tmp/train_artifacts/tmp/stage1_v3_8_core2_cleanheldout_restart/`
- Pathway artifacts: `results/runpod_tmp/eval_artifacts/tmp/exp022_eval/pathway/`
- Sampled anti-repeat eval: `results/runpod_tmp/eval_artifacts/tmp/exp022_eval/sampled_rep/samples.jsonl`
- Greedy no-repeat eval: `results/runpod_tmp/eval_artifacts/tmp/exp022_eval/greedy_no_repeat/samples.jsonl`
- Local reports:
  - `results/pathway_analysis.json`
  - `results/pathway_cosines.json`
  - `results/eval_report_sampled.json`
  - `results/eval_report_greedy.json`
  - `results/eval_report_train_samples.json`

## Run

022 used the v3.8 clean-heldout split and restarted from the 006 no-trunk
checkpoint (`checkpoints/stage1_gemma_no_trunk/final.pt`). The first reliable
run launched on RunPod pod `18dobdao5syd9f`, synced the local source tree to
`/tmp/text-ip-adapter-022`, read data/checkpoints from `/workspace`, wrote all
train/eval artifacts under `/tmp`, downloaded artifacts locally, and terminated
the pod.

The initial runner hung after the completed train command had already produced
`final.pt`. Eval and download were continued manually from the same live pod;
the manifest is marked `completed_manual_recovery`.

## Pathway Result

Aggregate pathway diagnostic over 32 clean-heldout probes:

| variant | cos_z | cos_K_first | cos_K_last | cos_V_first | cos_V_last | gen_J |
|---|---:|---:|---:|---:|---:|---:|
| swap | 0.437 | 0.595 | 0.382 | 0.521 | 0.394 | 0.056 |
| zero | 0.000 | 0.401 | -0.282 | 0.344 | -0.175 | 0.000 |
| random | 0.107 | 0.306 | 0.117 | 0.199 | 0.116 | 0.008 |
| code | 0.066 | 0.159 | 0.014 | 0.122 | -0.016 | 0.011 |

Register split for `cos_K_last_swap`:

| register | n | cos_z_swap | cos_K_last_swap | random | code | gen_J |
|---|---:|---:|---:|---:|---:|---:|
| poetry | 16 | 0.285 | 0.293 | 0.119 | -0.065 | 0.024 |
| screenplay | 16 | 0.590 | 0.470 | 0.116 | 0.092 | 0.087 |

This passes the pre-registered pathway gate: aggregate `cos_K_last_swap <= 0.55`,
both registers below `0.60`, and code/random are separated.

## Surface Evals

Sampled anti-repeat eval (`temperature=0.8`, `top_p=0.9`,
`repetition_penalty=1.12`, `no_repeat_ngram_size=3`):

- T1 discrimination: PASS (`mean_jaccard=0.002`)
- T3 surface carryover: WEAK (`17/32` own wins)
- T4 memorization/leak: PASS/PASS (`0%` / `0%`)
- repeat-3: mean `0.000`, max `0.020`, `0/128` above `0.20`

Greedy no-repeat eval:

- T1 discrimination: PASS (`mean_jaccard=0.039`)
- T3 surface carryover: WEAK (`19/32` own wins)
- T4 memorization/leak: PASS/PASS (`0%` / `0%`)

Train-loop samples without anti-repeat decoding still repeat heavily, so final
quality should be judged from the sampled/greedy checkpoint evals, not the raw
training samples.

## Qualitative Read

The direction is promising but not claim-ready.

Positive:

- The clean-heldout pathway result is the best core2 signal so far.
- Poetry now separates strongly numerically (`0.293`) instead of carrying the
  aggregate weakness.
- Sampled anti-repeat outputs have essentially no mechanical looping.
- Screenplay outputs usually preserve screenplay formatting.

Remaining problems:

- Surface T3 is still WEAK; the outputs are different per reference, but not
  reliably proven to match author style.
- Poetry sometimes becomes archaic/prose-like literary imitation rather than
  actual poem form.
- Screenplay generations are often plausible but generic scene text.
- The full-probe in-training sample sweeps were wasteful: step-0, step-500, and
  final sampling dominated wall time.

## Decision

022 is **partially_confirmed / pathway-positive / style-unproven**.

It answers the contamination concern: after removing 006 warmstart author
overlap, the no-trunk core2 adapter still produces a strong reference-specific
K/V pathway. It does not yet prove C1 because T3 remains weak and LLM-judge
T2/T3b was unavailable locally.

## Next Best Bet

1. Run a cheap dual-judge or at least stronger single-judge audit on the 022
   sampled and greedy outputs, focused on T3b style match against own vs swap
   references.
2. If judge audit is encouraging, run a faster 022b continuation/replicate with
   `sample_every: 0` or a tiny in-training probe set, preserving full final
   pathway and sampled eval.
3. If judge audit is weak, do not widen the encoder yet. First inspect the
   instruction/objective mismatch: many outputs are genre/register-correct but
   not author-specific enough.
