# Learnings

Status: completed/refuted.

The experiment exists because 013 separated the failure:

- data corruption was real and fixed enough to proceed;
- the reference pathway remains healthy;
- final generations still repeat.

This run tested whether contrastive pressure is part of the repetition failure.

Result: disabling contrastive is not the fix.

- Final samples still repeat across poetry, screenplay, and speech.
- Pathway separation regressed sharply versus 013:
  - `mean_cos_z_swap=0.720`
  - `mean_cos_K_first_swap=0.861`
  - `mean_cos_K_last_swap=0.792`
  - `mean_cos_K_last_random=0.126`
  - `mean_cos_K_last_code=0.201`
- 013 contrastive-on was much healthier on the same corrected core3 corpus:
  `mean_cos_K_last_swap=0.398`, random=-0.039, code=0.044.

Conclusion: contrastive loss at weight 0.1 should stay on. It is doing useful
anti-collapse work, and removing it does not solve repetition.

Next best bet: run a decoding/objective diagnostic with data and checkpoint held
fixed. First test whether anti-repetition generation controls rescue 013
outputs. If yes, fold those controls into evaluation and consider training-time
sampling/decoding alignment. If no, change the training target/objective rather
than the corpus.
