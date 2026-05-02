# Experiment 022 - Broader Clean Split Restart

Status: completed with manual orchestration recovery. Result:
pathway-positive, style-unproven.

## Question

Can the no-trunk adapter show cleaner author-disjoint core2 conditioning when
the heldout authors are selected to be unseen by the 006 warmstart train set?

## Why This Exists

021 found the current core2 eval is too narrow and partly contaminated by
warmstart exposure. v3.8 fixes that by holding out only authors absent from
`data/pairs/train.llm.jsonl`, the 006 no-trunk training split.

## Method

- Dataset: `data/pairs_v3_8_core2_cleanheldout`.
- Init: `checkpoints/stage1_gemma_no_trunk/final.pt`.
- Train 1,000 steps on core2 only.
- Output to `/tmp/stage1_v3_8_core2_cleanheldout_restart` to avoid the
  network-volume write quota observed during 021.
- Eval on `probes_balanced.jsonl` (32 probes, 8 heldout authors/register).

## Decision Rule

Promising if:

- aggregate `cos_K_last_swap <= 0.55`;
- both poetry and screenplay are below `0.60`;
- random/code stay near zero or negative;
- sampled outputs stay low-repeat and T4 PASS/PASS.

If it fails, the next move is not more continuation training. It is either a
stronger author-negative objective or a larger architectural change.

## Result

The clean `/tmp` RunPod run completed on pod `18dobdao5syd9f`; artifacts are in
`results/runpod_tmp/`, and the pod was terminated.

Pathway over 32 clean-heldout probes:

- aggregate `cos_K_last_swap=0.382`;
- poetry `cos_K_last_swap=0.293`;
- screenplay `cos_K_last_swap=0.470`;
- random/code `cos_K_last` are `0.117` / `0.014`;
- sampled anti-repeat eval has T1 PASS, T4 PASS/PASS, and near-zero repetition.

This passes the pre-registered pathway gate and answers the warmstart
contamination concern positively. It is not a C1 win yet: surface T3 is still
WEAK, and qualitative samples are often register-correct but not reliably
author-style-specific.

See `results/analysis_summary.md` for the full readout.

## Ops Note

The reliable launch pattern is now clear: sync the local project tree directly
to `/tmp`, symlink `/workspace` data/checkpoints, write all train/eval outputs
under `/tmp`, download by SFTP, and terminate. Do not run editable installs or
write artifacts inside `/workspace`.
