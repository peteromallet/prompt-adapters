# Learnings

Status: completed, partially confirmed.

v3.4 artifact cleanup is the first post-v3.3 change that improves generation
quality without breaking the pathway. The smoke kept the contrastive-on
reference channel alive (`cos_K_last_swap=0.502`; random/code near zero or
negative) and sampled anti-repeat decoding removed the loop pathology
(`repeat3_mean=0.002`, repeated-line mean `0.0` for adapter outputs).

The result is not a claim win. Surface T3 still fails (`7/15`, mean advantage
approximately zero), LLM judges were skipped, and manual samples show residual
artifacts: screenplay page numbers/continuations, numeric residue in one poem,
and register-level style imitation more than reliable author-level style.

Decision: proceed to a longer v3.4 run with the same no-trunk warmstart and
contrastive weight `0.1`, then require n>=20 dual-judge T2/T3b before treating
it as evidence for C1. Do not spend more runs on contrastive-off; 014 already
showed it damages the pathway.
