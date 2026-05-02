# Learnings

Status: completed; partially_confirmed.

v3.8 answered the contamination concern from 021 in the positive direction.
Heldout authors have zero overlap with the 006 warmstart train set, and after
restarting from 006 the pathway stayed strong: aggregate
`cos_K_last_swap=0.382`, poetry `0.293`, screenplay `0.470`, with random/code
well separated (`0.117` / `0.014`).

The result is still style-unproven. Sampled anti-repeat outputs are low-repeat
and T4-clean, but surface T3 remains WEAK and manual read says many outputs are
register-correct rather than author-style-specific. This is now a quality/judge
question, not a global projector-collapse question.

Operational learning: the network volume can read existing checkpoints/data but
fails on small writes in some paths. Reliable RunPod pattern: sync local source
directly to `/tmp`, symlink `/workspace` data/checkpoints, write outputs to
`/tmp`, SFTP-download artifacts, and terminate. Full 32-probe in-training
sampling is too expensive; keep full probes for final eval and use
`sample_every: 0` or a tiny probe set during training.
