# Experiment 023 - Eval-Clean Probe Audit

Status: completed.

## Question

Did dirty v3.8 probe references, especially the Christina Rossetti footnote
reference, distort the 022 readout?

## Method

- Build `data/pairs_v3_9_core2_evalclean` from v3.8.
- Keep train/val/test unchanged.
- Rebuild only balanced probes, using clean heldout target chunks as references.
- Re-evaluate the 022 final checkpoint without retraining.

## Result

Cleaning probes removed obvious reference artifacts (`dirty_refs=0`) and made
some sampled poetry outputs look less footnote-like. But the numeric pathway got
worse:

- v3.8 probes: aggregate `cos_K_last_swap=0.382`, poetry `0.293`, screenplay
  `0.470`.
- v3.9 eval-clean probes: aggregate `0.541`, poetry `0.647`, screenplay
  `0.435`.

Random/code remain separated (`0.047` / `-0.079`), so this is not global
collapse. It is specifically weak same-register own-vs-swap separation when the
references are cleaner and more author-comparable.

## Decision

023 is negative/informative. 022 was real pathway-positive evidence, but its
strongest number was probe-sensitive. The poetry problem is not only dirty
references; the current objective still does not learn robust author-specific
style binding for clean poetry refs.
