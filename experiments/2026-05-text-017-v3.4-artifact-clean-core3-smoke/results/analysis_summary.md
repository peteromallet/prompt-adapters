# 017 Analysis Summary

Status: completed, partially confirmed.

## Artifacts

- Training artifacts:
  `results/download_smoke_training/workspace/text-ip-adapter/experiments/017_smoke_training_artifacts/`
- Pathway probe:
  `results/download_pathway_n15/workspace/text-ip-adapter/experiments/v3_4_artifact_clean_core3_pathway_n15/`
- Sampled anti-repeat eval:
  `results/download_sampled_antirepeat/workspace/text-ip-adapter/eval_runs/2026-05-text-017-v3.4-sampled-antirepeat/`
- Local eval report: `results/eval_report.json`

## Pathway

Compared with 013, the pathway is slightly weaker on same-register swap but
still in the acceptable band for a smoke:

| variant | cos_z | cos_K_first | cos_K_last | gen_J |
| --- | ---: | ---: | ---: | ---: |
| swap | 0.499 | 0.542 | 0.502 | 0.177 |
| zero | 0.000 | 0.419 | -0.140 | 0.004 |
| random | -0.030 | 0.004 | -0.054 | 0.002 |
| code | 0.015 | -0.004 | -0.056 | 0.006 |

Interpretation: not globally collapsed. Out-of-domain references do not map to
the same prefix. Same-register swaps remain related, as expected.

## Sampled Generation

The sampled anti-repeat profile wrote 60 rows: 15 each for `adapter`,
`adapter_swap`, `no_ref`, and `prompted_baseline`.

Adapter metrics:

- `repeat3_mean=0.002`
- repeated-line mean `0.0`
- empty rows `0`
- heuristic artifact rows `2/15`

Qualitative read:

- Poetry is recognizably verse in 4/5 adapter rows, with one clear prose drift
  and one numeric residue row (`13`, `2050`).
- Screenplay is consistently screenplay-shaped, but still has page-number and
  continuation residue in some rows.
- Speech is the strongest register: all 5 adapter rows are plausible
  nineteenth-century public-address prose, though author-level specificity is
  not proven.
- No-ref and prompted baselines often drift into generic school-answer prose,
  factual summaries, or instruction-answer format. The adapter is doing real
  register steering.

## Eval Battery

`scripts/eval_probes.py --skip-llm-judge` on the downloaded artifacts:

- T1 discrimination: PASS, adapter/swap `mean_jaccard=0.004`.
- T3 surface carryover: FAIL, `7/15`, mean advantage approximately zero.
- T4 target memorization: PASS, `0.0%`.
- T4 reference leak: PASS, `0.0%`.
- T5 loss curve: SLOW, first quartile `2.735`, last quartile `2.255`,
  improvement `17.5%`.
- T2 and T3b LLM judge: skipped, no judge key available.

## Decision

Proceed to a longer v3.4 artifact-clean core3 training run with contrastive
kept on. The current direction is promising but still provisional: the smoke
proves "healthy pathway plus much cleaner sampled generations", not
"author-level style transfer".

Required next gates:

1. n>=20 pathway probe, including register breakdown.
2. n>=20 sampled anti-repeat eval.
3. Dual-judge T2/T3b, not Haiku-only.
4. Manual artifact audit of failures, especially screenplay numeric residue and
   poetry prose drift.
