# Learnings

Status: completed; negative/informative.

v3.9 eval-clean probes removed the obvious dirty-reference confound in v3.8.
The result did not rescue 022 into a clean C1 win. Instead, own-vs-swap pathway
separation worsened from `cos_K_last_swap=0.382` to `0.541`, with poetry
weakening to `0.647`.

This says the adapter can separate pathological references and many screenplay
refs, but clean within-register author-style separation is still fragile. The
next training run should not be a wider encoder by default. It should first
attack the objective/eval mismatch: make references clean, make instructions
less content-word brittle, and add a direct style-alignment or author-negative
signal instead of relying only on next-token CE plus generic K/V contrastive.

Operationally, checkpoint-only RunPod eval from a local downloaded checkpoint is
now scripted in `text-ip-adapter/scripts/eval_022_checkpoint_v39_runpod.py`.
