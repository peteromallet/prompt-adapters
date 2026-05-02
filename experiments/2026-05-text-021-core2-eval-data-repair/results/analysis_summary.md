# 021 Analysis Summary

Status: completed.

## Artifacts

- Repaired dataset: `text-ip-adapter/data/pairs_v3_7_core2_repaired/`
- Checkpoint outputs: `results/checkpoints/`
- Numeric summary: `results/checkpoint_summary.json`
- Local eval reports:
  - `results/eval_report_018_step1000.json`
  - `results/eval_report_020_final.json`

RunPod pods used for eval/recovery were terminated. The first eval hit a
network-volume write quota while writing the `020_final` sampled file; recovery
downloaded existing artifacts via SFTP and reran the missing sampled eval on
container `/tmp`.

## Data Repair

v3.7 fixed two issues found after 020:

- removed 29 dense timecode-contaminated screenplay rows;
- stripped screenplay page/revision debris from train rows;
- rebuilt probes to cycle unique heldout reference documents where available.

Probe diversity improved from repeated same-reference poetry pairs to 9 unique
poetry reference docs and 5 unique screenplay reference docs. Screenplay remains
limited because three of the four heldout screenplay authors only have one
unique reference doc.

## Checkpoint Comparison

Repaired core2 n20 pathway:

| checkpoint | cos_z_swap | cos_K_last_swap | random | code | gen_J | T3 | T4 | repeat3 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| 018 step1000 | 0.523 | 0.598 | -0.091 | -0.098 | 0.075 | FAIL 11/20 | PASS/PASS | 0.0016 |
| 020 final | 0.461 | 0.502 | -0.071 | -0.091 | 0.051 | WEAK 11/20 | PASS/PASS | 0.0006 |

`020_final` remains the better checkpoint, but the repaired probe makes the old
020 aggregate less rosy (`0.502`, not `0.440`).

## Register Split

`cos_K_last_swap`:

| checkpoint | poetry | screenplay |
| --- | ---: | ---: |
| 018 step1000 | 0.529 | 0.667 |
| 020 final | 0.522 | 0.483 |

The previous 020 story was partly a probe artifact. Poetry is better than the
v3.6 probe suggested (`0.522` vs `0.633`), while screenplay is harder once the
probe uses more varied references (`0.483` vs `0.248`). The real state is not
"screenplay solved, poetry bad"; it is "core2 is pathway-positive but still not
author-style-proven."

## Qualitative Read

Both checkpoints produce clean, low-repeat poetry and screenplay. `020_final`
is cleaner than `018_step1000` and avoids the obvious page/image artifacts in
the sampled outputs. No target memorization or reference leakage appeared.

Surface T3 remains too weak to carry the claim. A dual-judge T2/T3b pass is
still required before upgrading C1.

## Decision

021 supports keeping `020_final` as the best current checkpoint, but it also
shows the eval set is too narrow for strong claims. Do not widen the encoder
yet.

Next best bet:

1. Build a future clean split with more heldout authors/reference docs per
   register. This probably requires a less-contaminated restart checkpoint,
   because current warmstarts have already trained on many candidate heldout
   authors.
2. In parallel, run dual-judge T2/T3b on the current repaired n20 to decide
   whether the clean qualitative outputs are genuinely style-matched.
3. If judge signal is still weak, run a poetry/core2 negative-pair objective
   ablation rather than scaling more steps.
