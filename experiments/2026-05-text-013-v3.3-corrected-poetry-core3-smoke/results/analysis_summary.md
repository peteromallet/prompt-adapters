# Experiment 013 Analysis Summary

Status: completed on 2026-04-25.

## Result

v3.3 corrected-poetry core3 is **pathway-positive but generation-quality-negative**.

The data repair was necessary and real:

- the corrected poetry source list removed bogus Gutenberg IDs;
- the core3 corpus passed author-disjoint heldout gates;
- targeted poetry contamination scan returned `0` known bad markers;
- poetry outputs are now recognizably verse-shaped instead of geography/index
  or prose artifacts.

But the training objective still produces repetition and generic content.

## Pathway

Post-training balanced n=15 pathway:

| metric | value |
| --- | ---: |
| `mean_cos_z_swap` | 0.409 |
| `mean_cos_K_first_swap` | 0.469 |
| `mean_cos_K_last_swap` | 0.398 |
| `mean_cos_K_last_random` | -0.039 |
| `mean_cos_K_last_code` | 0.044 |
| `mean_gen_jaccard_swap` | 0.036 |

Interpretation: the reference signal is not globally collapsed. The encoder,
projector, and injected K/V path still discriminate references.

## Qualitative

Final samples are not acceptable:

- poetry repeats phrases such as "Little God" or "Love is a thing";
- screenplay has correct screenplay shape but repeats local beats;
- speech has correct formal-address shape but repeats sentences;
- no-ref generations remain generic summaries or repeated prompt-style prose.

Representative final examples live in:

- `results/smoke_training/samples.jsonl`
- `results/v3_3_corrected_poetry_core3_pathway_balanced_n15/generations.jsonl`

## Decision

Do **not** run a full v3.3 training run.

The next best bet is not more data-only cleanup. Data cleanup fixed the obvious
corruption, and the pathway is healthy. The remaining failure is likely in the
objective/decoding/training setup: next-token loss with the current prompts and
teacher-forced targets is not enough to teach non-repetitive style-conditioned
generation.

Recommended next experiment:

1. keep v3.3 corrected core3 data;
2. reduce startup/frequent probe cost to a small smoke probe;
3. test an objective/decoding intervention, such as:
   - supervised CE only with contrastive disabled as an ablation;
   - stronger anti-repetition filtering/penalty in generation probes;
   - shorter target windows or packed excerpt targets;
   - add a repetition penalty/entropy regularizer if training supports it;
   - LLM-regenerated instructions that specify form and task more concretely.

The immediate first ablation should be cheap: same data, same no-trunk
warmstart, `contrastive_weight=0`, small probe set, 500-1000 steps. If samples
remain repetitive, the issue is not contrastive competition.
