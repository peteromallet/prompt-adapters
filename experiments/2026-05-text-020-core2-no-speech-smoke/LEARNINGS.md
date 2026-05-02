# Learnings

Status: completed.

Deliberate register isolation worked as a diagnostic. Removing speech produced
a pathway-positive core2 run (`cos_K_last_swap=0.440`, random/code negative or
near zero) and eliminated the speech-driven T4 false-positive pattern.

The result is not a full style win. The aggregate is carried by screenplay
(`cos_K_last_swap=0.248`), while poetry remains middling (`0.633`). Surface T3
is WEAK (`11/20`) and LLM judges were unavailable locally.

Next best bet: repair/audit core2 rather than widen the encoder. Strip
screenplay page/image artifacts, audit poetry author-pair separability, and
re-evaluate the best checkpoints before spending on another training run.
