# Experiment 003 — Learnings

## Headline
**The projector is the bottleneck.** Experiment 002's failure to style-condition on the reference (T3b coin flip despite T2 PASS) is not an encoder problem, not an injection problem, and not a data problem — the projector is collapsing diverse encoder outputs into near-identical K/V tensors.

## The decisive data

n=10 probes, 5 reference variants each (own, swap, zero, random, code), measuring pairwise cosine similarity vs the own-reference outputs at each pathway layer.

| Variant | cos_z | cos_K_first | cos_K_last | gen_Jaccard |
|---|---|---|---|---|
| swap (same-domain, different author) | 0.766 | 0.978 | 0.963 | 0.127 |
| zero (null prefix) | 0.000 | 0.908 | 0.817 | 0.003 |
| random (gibberish tokens) | 0.382 | 0.805 | 0.770 | 0.003 |
| code (Python, out-of-domain) | 0.420 | 0.934 | 0.853 | 0.009 |

### Reading it

- **Encoder is fine.** cos_z varies appropriately with input — 0.766 for similar-domain swap, 0.38 for random, 0.42 for code, 0.0 for zero. The encoder produces input-sensitive latents. Not collapsed.
- **Projector is squashing.** K/V cosines are 0.71–0.98 across all variants including zero-prefix. The projector maps wildly different z inputs (including the zero vector) into nearly the same K/V output direction. It's behaving as an almost-constant function of the reference.
- **Injection and base model are fine.** Zero-prefix vs own-reference differ by gen_Jaccard=0.003 (almost no n-gram overlap in output) despite 91% K/V cosine on layer 1 — the base model is very sensitive to the small K/V differences that do exist. The downstream stack works; the problem is upstream.

### The mechanism

The projector's shared MLP trunk + per-layer linear heads is collapsing the encoder's diversity into a low-rank output subspace. Training pressure: next-token CE on pairs pushes the projector toward "produce a literary-register K/V" rather than "encode THIS reference." The trunk learns to be a style-register transform, not a reference-encoder. The per-layer heads inherit that constraint.

## What this means for experiments 001 and 002

- **Experiment 002's T2 PASS (80% vs prompting) was register bias, not reference conditioning.** The adapter produces "generic literary voice" for any input, which happens to beat the prompted baseline's awkward "Write in the style of: <ref>" format. True reference conditioning requires the projector output to vary meaningfully across references — it doesn't.
- **C1 (adapter beats prompting on style transfer) should be downgraded** from "first positive evidence" back toward "testing." The literal statement is technically supported, but the spirit of the claim (reference-driven style) is not.
- **T2 alone is an insufficient gate.** Capability tests (α-blend, strength-dial) are even more load-bearing than previously framed — they would have caught this failure immediately. α-blending with a collapsed projector would produce no smooth interpolation.

## Corrections to prior plans

### Experiment 003 — revised scope

Originally planned: contrastive loss on encoder outputs.
New plan: projector bottleneck fix. Two sub-options:

- **003a — contrastive loss on projector K/V outputs.** Within each batch, pull apart the K/V tensors produced from different-author references. Minimal architectural change; adds a loss term that explicitly rewards reference-specific K/V divergence. Cheapest intervention.
- **003b — architectural fix.** Remove the shared MLP trunk in PrefixProjector; have each per-layer head project z → K/V directly (plus optional per-layer norm). Eliminates the bottleneck structurally. More invasive, requires recheck of zero-init no-op property.

Run 003a first. If K/V cosine across refs doesn't drop meaningfully by end of training, move to 003b.

### Data scale (experiment 004) deprioritized

More data alone will not fix the projector bottleneck — more data would just train the same squashing function more thoroughly. Keep 004 in the queue, but it's no longer the next experiment.

## Process notes (honest)

- This experiment was not launched via tools/launch-experiment.sh. The script was skipped; manifest backfilled retroactively. Marked backfilled=true. First stress-test of PROCESS.md discipline and I (the operator) failed it on the first try.
- What was fixed: text-ip-adapter initialized as git repo; the probe script committed (SHA f3dc198) to have a stable reference-commit; launch_manifest.json reconstructed from known run-time state; results copied to results/; this LEARNINGS written; tags exp-003-launch and exp-003-finalized created retroactively.
- Lesson for scripts: launch-experiment.sh assumes a training-style config with data_paths pointing at train/val/test jsonl. A diagnostic experiment has a different config shape. Either (a) extend the script to accept type: diagnostic configs, or (b) add a separate probe-experiment.sh. Tracking as a tool-TODO, not a blocker.

## Cost summary

- Pod time: ~10 minutes (no training; just inference across 50 generations).
- LLM judge: N/A (analysis is pure numeric pairwise cosine; no API calls).
- Total: ~$0.12 (pod hourly rate × 10 min).
