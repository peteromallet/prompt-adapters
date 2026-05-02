# Experiment 023 Analysis Summary

Status: completed.

## Artifacts

- Dataset: `text-ip-adapter/data/pairs_v3_9_core2_evalclean/`
- Run manifest: `results/runpod_v39_eval/launch_manifest.json`
- Pathway artifacts:
  `results/runpod_v39_eval/eval_artifacts/tmp/exp023_v39_eval/pathway/`
- Sampled anti-repeat eval:
  `results/runpod_v39_eval/eval_artifacts/tmp/exp023_v39_eval/sampled_rep/samples.jsonl`
- Local reports:
  - `results/eval_report_sampled.json`
  - `results/stylometric_sampled_char.json`
  - `results/stylometric_sampled_word.json`

## Why This Ran

022 looked strong numerically but manual audit found that some poetry probes used
dirty references. The worst case was Christina Rossetti: v3.8 used a footnote
/ Dante block as the style reference, and adapter outputs mimicked footnotes,
epigraphs, and literary prose. v3.9 rebuilt probes with clean heldout target
chunks as references while leaving train/val/test unchanged.

## Pathway

| probe set | aggregate | poetry | screenplay | random | code |
|---|---:|---:|---:|---:|---:|
| v3.8 original | 0.382 | 0.293 | 0.470 | 0.117 | 0.014 |
| v3.9 eval-clean | 0.541 | 0.647 | 0.435 | 0.047 | -0.079 |

The v3.9 result still separates random/code references, so the pathway is not
globally collapsed. The regression is same-register own-vs-swap style
separation, especially poetry.

## Surface Evals

Sampled anti-repeat eval on v3.9:

- T1 discrimination: PASS (`mean_jaccard=0.001`)
- T3 surface carryover: FAIL (`15/32` own wins)
- T4 memorization/leak: PASS/PASS (`0%` / `0%`)
- repeat-3: mean `0.0004`, max `0.0139`

Stylometric TF-IDF audit:

- adapter char own-ref win rate: `21/32`
- adapter word own-ref win rate: `19/32`
- adapter poetry word own-ref win rate: `8/16`
- adapter screenplay word own-ref win rate: `11/16`
- prompted baseline is competitive or stronger on several own-reference
  similarity measures.

## Interpretation

Cleaning probes improves the face validity of some poetry samples, but it does
not produce a claim-ready result. The stronger conclusion is that 022 is
probe-sensitive: the adapter reliably changes outputs per reference and
separates pathological references, but clean same-register author-style binding
is still not robust.

## Next

Do not jump straight to wider encoder. The next training hypothesis should
target objective/data alignment:

1. Clean reference docs in train as well as eval, not only targets.
2. Make instructions less brittle than two extracted content words.
3. Add an own-vs-swap style alignment or author-negative objective, because
   generic K/V contrastive separates references without guaranteeing separation
   along the author-style axis.
