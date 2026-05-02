# Experiment 019 - Balanced Checkpoint Comparison

Status: completed. Eval pod `2wk8ccy36w75cq` was terminated after artifact
download.

## Question

Did 018 fail because the 3000-step continuation overtrained, or because 017's
positive read was probe-dependent?

## Why This Exists

018 found two things at once:

- the 3000-step final checkpoint has weak same-register own/swap pathway
  separation on n20 (`cos_K_last_swap=0.909`);
- the n20 default probe builder was flawed, over-selecting two authors per
  register and repeating author pairs.

So the next move is not more training. It is a controlled checkpoint comparison
on a better probe set.

## Method

Evaluate these checkpoints on
`data/pairs_v3_5_artifact_clean_core3/probes_balanced_n21.jsonl`:

- 017 final;
- 018 step 500;
- 018 step 1000;
- 018 final.

For each checkpoint:

- run `probe_conditioning.py` pathway diagnostics;
- run sampled anti-repeat checkpoint eval;
- run local eval battery with LLM judges skipped unless a judge key is present.

## Decision Rule

If early 018 is better than final, use early stopping or lower LR. If 017 also
fails on balanced n21, the 017 optimism was probe-dependent and we should fix
evaluation/data before more GPU training. If 017 is good and all 018 checkpoints
are worse, continuation from 017 is actively harmful.

## Results

Balanced n21 removed the misleading n20 result from 018. The 018 final
checkpoint is not catastrophically collapsed under a balanced probe, but
`018_step1000` is the best checkpoint.

| checkpoint | cos_K_last_swap | random | code | adapter repeat3 | T3 surface | T4 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 017 final | 0.639 | -0.099 | -0.106 | 0.0016 | FAIL 9/21 | mem WEAK, leak PASS |
| 018 step500 | 0.641 | -0.105 | -0.056 | 0.0000 | FAIL 7/21 | mem WEAK, leak PASS |
| 018 step1000 | 0.609 | -0.114 | -0.070 | 0.0015 | WEAK 13/21 | mem WEAK, leak PASS |
| 018 final | 0.637 | -0.107 | -0.041 | 0.0005 | WEAK 11/21 | mem WEAK, leak PASS |

The register breakdown is the real diagnosis:

| checkpoint | poetry | screenplay | speech | poetry+screenplay mean |
| --- | ---: | ---: | ---: | ---: |
| 017 final | 0.634 | 0.306 | 0.978 | 0.470 |
| 018 step500 | 0.655 | 0.293 | 0.974 | 0.474 |
| 018 step1000 | 0.640 | 0.216 | 0.972 | 0.428 |
| 018 final | 0.626 | 0.312 | 0.974 | 0.469 |

Speech own/swap is nearly collapsed for every checkpoint. Poetry and screenplay
are much healthier, especially screenplay at step1000.

The T4 memorization warnings are mostly formulaic speech salutations, e.g.
overlaps on "Gentlemen of the Senate and Gentlemen of the House of
Representatives." Treat them as a real speech-data warning, not as strong target
memorization evidence.

## Decision

Use `018_step1000` as the best current checkpoint for balanced eval. Do not
train longer from it without a speech intervention. The next training bet should
either exclude speech temporarily or repair speech prompts/salutation handling
before any wider-encoder architecture run.
