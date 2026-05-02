# 019 Analysis Summary

Status: completed.

## Artifacts

- Pathway outputs:
  `results/download_pathways/workspace/text-ip-adapter/experiments/019_balanced_checkpoint_comparison/`
- Sampled outputs:
  `results/download_sampled/workspace/text-ip-adapter/eval_runs/019_balanced_checkpoint_comparison/`
- Numeric summary: `results/checkpoint_summary_with_eval.json`
- Register summary: `results/register_pathway_summary.json`

## Headline

`018_step1000` is the best current checkpoint, and speech is the dominant weak
register.

## Checkpoint Table

| checkpoint | cos_z_swap | cos_K_last_swap | random | code | gen_J | repeat3 | T3 | T4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 017 final | 0.587 | 0.639 | -0.099 | -0.106 | 0.168 | 0.0016 | FAIL 9/21 | mem WEAK, leak PASS |
| 018 step500 | 0.591 | 0.641 | -0.105 | -0.056 | 0.121 | 0.0000 | FAIL 7/21 | mem WEAK, leak PASS |
| 018 step1000 | 0.566 | 0.609 | -0.114 | -0.070 | 0.110 | 0.0015 | WEAK 13/21 | mem WEAK, leak PASS |
| 018 final | 0.579 | 0.637 | -0.107 | -0.041 | 0.076 | 0.0005 | WEAK 11/21 | mem WEAK, leak PASS |

All sampled adapter outputs remain low-repeat. The deciding signal is pathway
plus register breakdown, not repetition.

## Register Breakdown

`cos_K_last_swap` by register:

| checkpoint | poetry | screenplay | speech | poetry+screenplay mean |
| --- | ---: | ---: | ---: | ---: |
| 017 final | 0.634 | 0.306 | 0.978 | 0.470 |
| 018 step500 | 0.655 | 0.293 | 0.974 | 0.474 |
| 018 step1000 | 0.640 | 0.216 | 0.972 | 0.428 |
| 018 final | 0.626 | 0.312 | 0.974 | 0.469 |

Speech is effectively collapsed across all checkpoints. Screenplay is strong,
especially at `018_step1000`. Poetry is middling but not collapsed.

## T4 Caveat

The T4 `WEAK` warnings are concentrated in speech probes and mostly hit
formulaic salutations:

- "Gentlemen of the Senate and Gentlemen of the House of Representatives"
- "Fellow-Citizens of the Senate and House of Representatives"

This is not strong evidence of target memorization. It is evidence that speech
data/eval contains boilerplate formulas that defeat the current n-gram leak
metric.

## Decision

Use `018_step1000` as the best current checkpoint for further evaluation.

Do not run wider encoder yet. The next training move should isolate or repair
speech:

1. Build a poetry+screenplay core2 dataset from v3.5.
2. Train/evaluate from `018_step1000` or the 017 final checkpoint on core2.
3. Separately repair speech by stripping salutations and/or building
   topic-specific speech prompts before putting it back into the main corpus.
