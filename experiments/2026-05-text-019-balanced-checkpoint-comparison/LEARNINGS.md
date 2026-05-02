# Learnings

Status: completed.

This experiment prevented a bad conclusion from 018's skewed n20 probe.
Balanced n21 shows 018 final is not catastrophically collapsed, but
`018_step1000` is the best current checkpoint.

The central blocker is now register-specific: speech own/swap remains nearly
collapsed (`cos_K_last_swap` around `0.97`) for every checkpoint, while
poetry+screenplay are much healthier (`0.428` mean at step1000). The next
training run should isolate speech rather than widening the architecture.

T4 warnings are also speech-specific and mostly salutation boilerplate, so the
leak/memorization metric needs a speech-formula exception or a separate
salutation-stripped speech eval.
