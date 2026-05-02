# Learnings

Status: completed; partially confirmed, but not claim-ready.

024a added a direct within-register author-style triplet loss to the 022
checkpoint and continued for 500 steps on v3.9. This was the right diagnostic,
but by itself it is not enough:

- aggregate `cos_K_last_swap`: `0.541` in 023 -> `0.522` in 024a
- poetry: `0.647` -> `0.572`
- screenplay: `0.435` -> `0.472`
- random/code stayed separated: `0.085` / `-0.024`
- sampled T1 PASS, T3 WEAK (`16/32` own wins), T4 PASS/PASS
- sampled repeat-3 stayed low: adapter mean `0.0008`, max `0.0149`

The triplet loss is active and moves the pathway a little, especially poetry,
but the effect is far smaller than needed for C1. The stronger conclusion is
that the training distribution is still misaligned: v3.9 kept the old brittle
two-word instructions and train-side artifact residue even though its probes
were clean.

024b tested the same continuation on `pairs_v4_core2_styleclean`, which strips
remaining train/val/test artifacts and replaces content-token instructions with
register-level style instructions. It did **not** improve the pathway:

- aggregate `cos_K_last_swap`: `0.535`
- poetry: `0.589`
- screenplay: `0.481`
- sampled T3 remained WEAK (`16/32`)
- stylometric adapter own-ref dropped to `20/32` char and `18/32` word

So the next hypothesis was that a short continuation from 022 is path-dependent:
022 has already learned on the old instruction/data distribution.

024c confirmed that hypothesis at the pathway level. Restarting from the
cleaner 006 no-trunk checkpoint on v4, with normal contrastive restored (`0.1`)
and stronger triplet pressure (`0.5`, margin `0.3`), produced the best clean
same-register pathway result so far:

- aggregate `cos_K_last_swap`: `0.360`
- poetry: `0.559`
- screenplay: `0.161`
- random/code: `0.007` / `-0.046`

This is a strong recovery for the architecture/objective pathway, especially
screenplay. But it is not a C1 win:

- poetry remains weak (`0.559`)
- sampled surface T3 is FAIL (`15/32` own wins)
- stylometric evidence is only mixed (`21/32` char own-ref, `19/32` word
  own-ref; prototype metrics are worse)
- prompted baseline remains competitive on several reference-similarity metrics

Next best bet: stop treating poetry and screenplay as one problem. Screenplay
now looks pathway-solved. Poetry needs a targeted repair: audit poetry author
separability, rebuild generic-instruction probes, and likely add a stronger
supervised author-class/prototype objective for poetry rather than more generic
triplet continuation.
