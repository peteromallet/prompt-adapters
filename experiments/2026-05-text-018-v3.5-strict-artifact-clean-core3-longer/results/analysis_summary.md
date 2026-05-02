# 018 Analysis Summary

Status: completed, inconclusive-to-negative.

## Artifacts

- Training artifacts:
  `results/download_training/workspace/text-ip-adapter/experiments/018_training_artifacts/`
- Pathway probe:
  `results/download_pathway_n20/workspace/text-ip-adapter/experiments/v3_5_artifact_clean_core3_pathway_n20/`
- Sampled anti-repeat eval:
  `results/download_sampled_antirepeat/workspace/text-ip-adapter/eval_runs/2026-05-text-018-v3.5-sampled-antirepeat/`
- Local eval report: `results/eval_report.json`

## Data Repair

Before launch, v3.4 was found to contain wrapped Gutenberg artifacts in heldout
reference text, for example a `[Picture: ...]` block split across two lines.
v3.5 applies a narrow persisted cleanup:

- remove wrapped picture/illustration/note blocks;
- remove standalone poetry page/year fragments;
- preserve author-disjoint split shape.

v3.5 counts:

- train: 8,817 rows;
- val: 282 rows;
- test: 247 rows;
- author-disjoint train/val/test: pass;
- core SHA: `a380657000c6d38a680d26e0378f9f35ac83181eb4b40591f9fe64c87fd5d4fa`.

## Training

Continuation from 017 final completed 3,000 steps and wrote `final.pt`.

Training loss is noisy and effectively plateaued by the repo metric:

- first quartile loss mean: `2.462`;
- last quartile loss mean: `2.388`;
- improvement: `3.0%`;
- T5 verdict: `PLATEAU`.

## Pathway

n20 default pathway summary:

| variant | cos_z | cos_K_first | cos_K_last | gen_J |
| --- | ---: | ---: | ---: | ---: |
| swap | 0.819 | 0.960 | 0.909 | 0.097 |
| zero | 0.000 | 0.471 | -0.182 | 0.008 |
| random | -0.037 | -0.026 | -0.095 | 0.004 |
| code | -0.057 | -0.047 | -0.100 | 0.000 |

Interpretation: out-of-domain references still separate, but same-register
own/swap separation is poor. This is not 014-style global collapse, but it is a
serious within-register/author-separation warning.

Caveat: the n20 default probe set is poorly balanced. It used mostly two
authors per register and repeated author pairs:

- poetry: 7 Sara Teasdale own rows, 1 Thomas Hardy own row;
- screenplay: 5 `12_and_holding` own rows, 1 `17_again` own row;
- speech: 5 Buchanan own rows, 1 J. Q. Adams own row.

A better file is now persisted:
`text-ip-adapter/data/pairs_v3_5_artifact_clean_core3/probes_balanced_n21.jsonl`.

## Sampled Generation

Adapter sampled outputs stayed clean:

- rows: 20 adapter, 20 adapter_swap, 20 no_ref, 20 prompted_baseline;
- adapter `repeat3_mean=0.001`;
- adapter repeated-line mean `0.0`;
- heuristic adapter artifact rows `1/20`.

Qualitative read: adapter outputs are still much more register-shaped than the
no-ref and prompted baselines, especially for poetry. This is not enough to
override the pathway and T4 warnings.

## Eval Battery

`scripts/eval_probes.py --skip-llm-judge`:

- T1 discrimination: PASS, adapter/swap `mean_jaccard=0.004`.
- T3 surface carryover: WEAK, `12/20`, mean advantage approximately zero.
- T4 target memorization: WEAK, `10.0%`.
- T4 reference leak: WEAK, `10.0%`.
- T5 loss curve: PLATEAU, `3.0%` improvement.
- T2/T3b LLM judge: skipped, no judge key available.

## Decision

Do not promote the 018 final checkpoint. The next best bet is an eval-only
checkpoint comparison, not another long train:

1. Evaluate 017 final on v3.5 balanced n21.
2. Evaluate 018 `step_500`, `step_1000`, and final on v3.5 balanced n21.
3. If early 018 beats final, use earlier stopping/lower LR.
4. If 017 also collapses on balanced n21, revise the 017 optimism as
   probe-dependent and focus on heldout probe design before more training.
