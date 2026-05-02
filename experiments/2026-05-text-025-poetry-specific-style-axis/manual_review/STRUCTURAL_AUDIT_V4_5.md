# v4.5 Structural Audit

Status: fixed into `text-ip-adapter/data/pairs_v4_5_poetry_structural_balanced`.

The manual v4.4 cleanup removed obvious bad text, but it left structural
duplication artifacts:

- Train had 1,268 rows but only 37 unique references; max repeated reference
  was 100 rows.
- Val had 348 rows but only 7 unique references; max repeated reference was 82
  rows.
- Test had 339 rows but only 6 unique references; max repeated reference was
  100 rows.
- Train still had 55 duplicate target-text groups; val had 98 duplicate
  target-text groups.
- The manually cleaned probe set had 15 rows because one bad John Masefield
  probe was correctly deleted.

Important clarification: the main issue was not usually many different inputs
with the same output. It was mostly the same reference input being paired with
many targets. There were also some repeated target texts, but those were a
secondary artifact.

## v4.5 Fix

Builder:

`text-ip-adapter/scripts/build_v4_5_poetry_structural_balanced.py`

Output:

`text-ip-adapter/data/pairs_v4_5_poetry_structural_balanced`

Rules:

- Keep all v4.4 manual edits/deletes.
- Deduplicate exact normalized `target_text` within each split.
- Cap train repeated references at 40 rows.
- Cap heldout repeated references at 30 rows.
- Cap train author rows at 60.
- Select rows by deterministic author round-robin so lower-count authors are
  not crowded out by high-count authors.
- Rebuild probes from cleaned heldout rows.

## Result

| Split | Rows | Unique refs | Max ref repeat | Target dup groups |
| --- | ---: | ---: | ---: | ---: |
| train | 727 | 31 | 40 | 0 |
| val | 183 | 7 | 30 | 0 |
| test | 134 | 6 | 30 | 0 |

Probe result:

- `probes_balanced_n16.jsonl`: 16 rows.
- 8 heldout authors.
- 2 probes per author.
- 2 swap references per swap author.
- No obvious artifact regex hits in reference, expected target, or swap
  reference.

Known residual limitation:

- Some training authors are genuinely data-thin after dedupe. T.S. Eliot has
  only 16 unique target texts, Rudyard Kipling 22, John Keats 25. This is now a
  real data-coverage limitation, not duplicate contamination.

## Next Experiment

Run v4.5 with the same objective/hyperparameters as the v4.3 successful repeat:

`text-ip-adapter/configs/stage1_v4_5_poetry_structural_balanced_triplet_restart006.yaml`

Interpretation:

- If pathway metrics stay good and sampled outputs improve, the residual v4.3
  problem was structural duplicate/reference overexposure.
- If pathway metrics degrade materially, v4.3 was benefiting from repeated
  reference exposure and we need a stronger objective or more clean unique
  poetry, not more duplicate pair expansion.
- If pathway metrics stay good but surface leakage remains, move next to
  stronger surface/style supervision rather than further easy data cleaning.
