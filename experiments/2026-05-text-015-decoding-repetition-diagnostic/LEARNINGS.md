# Learnings

Status: completed/partially_confirmed.

This experiment holds the 013 trained checkpoint fixed and tests whether
anti-repetition decoding controls can rescue the visible loops.

The intended interpretation is deliberately narrow:

- decoding helps: tune/evaluate generation controls before another training run;
- decoding fails: change the supervised target/objective, not the corpus or
  contrastive setting.

Result: decoding helps a lot on the narrow mechanical-loop failure.

- `greedy_no_repeat`: `repetition_penalty=1.15`, `no_repeat_ngram_size=3`.
- `sampled_rep`: `temperature=0.8`, `top_p=0.9`,
  `repetition_penalty=1.12`, `no_repeat_ngram_size=3`.
- Both variants reduced adapter line repetition to 0.0 across poetry,
  screenplay, and speech.
- The sampled variant is qualitatively more promising because it preserves
  longer outputs and less clipped prose.

This does not close the quality question. Remaining issues include instruction
leakage, generic/no-ref contamination, page-number artifacts, and uncertain
author-level style carryover.

Next: formalize sampled anti-repeat as the eval decoding profile and run a
small judge/human audit. If style remains weak, the next training run should
alter target construction/objective while retaining contrastive.
