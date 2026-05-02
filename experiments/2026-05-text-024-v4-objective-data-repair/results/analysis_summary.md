# Experiment 024 Analysis Summary

Status: completed.

## Artifacts

- 024a config: `text-ip-adapter/configs/stage1_v3_9_style_triplet_022continue.yaml`
- 024a RunPod artifacts: `results/runpod_style_triplet/`
- 024a sampled report: `results/eval_report_sampled.json`
- 024a stylometric reports:
  - `results/stylometric_sampled_char.json`
  - `results/stylometric_sampled_word.json`
- v4 dataset: `text-ip-adapter/data/pairs_v4_core2_styleclean/`
- v4 config: `text-ip-adapter/configs/stage1_v4_styleclean_triplet_022continue.yaml`
- v4 restart config: `text-ip-adapter/configs/stage1_v4_styleclean_triplet_restart006.yaml`

## 024a Result

| run | aggregate | poetry | screenplay | random | code |
|---|---:|---:|---:|---:|---:|
| 023 clean-probe baseline | 0.541 | 0.647 | 0.435 | 0.047 | -0.079 |
| 024a v3.9 triplet continuation | 0.522 | 0.572 | 0.472 | 0.085 | -0.024 |

The triplet objective moved poetry in the right direction but only modestly,
and screenplay moved backward. This is not a claim-ready improvement.

Sampled anti-repeat eval:

- T1 discrimination: PASS (`mean_jaccard=0.001`)
- T3 surface carryover: WEAK (`16/32` own wins)
- T4 memorization/leak: PASS/PASS (`0%` / `0%`)
- adapter repeat-3: mean `0.0008`, max `0.0149`

Stylometric TF-IDF:

- adapter char own-ref win rate: `22/32`
- adapter word own-ref win rate: `22/32`
- adapter poetry word own-ref win rate: `12/16`
- adapter screenplay word own-ref win rate: `10/16`
- no-ref and prompted baseline remain competitive on some similarity metrics,
  so this is not clean author-style proof.

## Data Finding

The v3.9 probes were clean, but v3.9 train/val/test still had the old
instruction pattern and residual artifacts:

- every instruction was the same 12-word template with two extracted content
  tokens;
- train target artifact hits included roman headings, page/image-like terms,
  Gutenberg markers, and a small number of footnote/ACT/SCENE artifacts;
- test refs still contained the known dirty Christina Rossetti footnote block,
  even though probes no longer used it.

`pairs_v4_core2_styleclean` is now staged:

- train rows: `7273` retained from `7305`
- val rows: `495` retained from `498`
- test rows: `479` retained from `497`
- instructions replaced with generic poetry/screenplay style requests
- roman headings stripped; serious footnote/Gutenberg residue removed from the
  main splits
- clean v3.9 balanced probes copied for comparability

## Interpretation

024a says objective repair is directionally plausible but insufficient on the
old train distribution.

## 024b Result

| run | aggregate | poetry | screenplay | random | code |
|---|---:|---:|---:|---:|---:|
| 024a v3.9 continuation | 0.522 | 0.572 | 0.472 | 0.085 | -0.024 |
| 024b v4 style-clean continuation | 0.535 | 0.589 | 0.481 | 0.058 | -0.013 |

024b did not improve the pathway. Sampled eval remained T1 PASS, T3 WEAK
(`16/32`), and T4 PASS/PASS. Stylometric own-ref evidence got weaker than 024a:
adapter own-ref was `20/32` by char n-grams and `18/32` by word n-grams.

This rejects the simple continuation story. Cleaning data and instructions is
not enough if the starting checkpoint is already shaped by the older
distribution.

## 024c Result

024c was the decisive restart:

- init: `checkpoints/stage1_gemma_no_trunk/final.pt` (006 no-trunk)
- data: `pairs_v4_core2_styleclean`
- contrastive: `0.1`
- style triplet: `0.5`, margin `0.3`
- steps: `1000`

| run | aggregate | poetry | screenplay | random | code |
|---|---:|---:|---:|---:|---:|
| 023 clean-probe baseline | 0.541 | 0.647 | 0.435 | 0.047 | -0.079 |
| 024a v3.9 continuation | 0.522 | 0.572 | 0.472 | 0.085 | -0.024 |
| 024b v4 continuation | 0.535 | 0.589 | 0.481 | 0.058 | -0.013 |
| 024c v4 restart from 006 | 0.360 | 0.559 | 0.161 | 0.007 | -0.046 |

024c materially beats the continuation runs and slightly beats 022's original
aggregate pathway number, but with clean probes and cleaner train data. This is
the strongest clean pathway result so far. The register split matters:
screenplay is now very strong; poetry remains the blocker.

Sampled anti-repeat eval:

- T1 discrimination: PASS (`mean_jaccard≈0.000`)
- T3 surface carryover: FAIL (`15/32` own wins)
- T4 memorization/leak: PASS/PASS (`0%` / `0%`)
- adapter repeat-3: mean `0.0033`, max `0.0330`

Stylometric TF-IDF:

- adapter char own-ref win rate: `21/32`
- adapter word own-ref win rate: `19/32`
- poetry word own-ref win rate: `11/16`
- screenplay word own-ref win rate: `8/16`
- prompted baseline remains stronger on some reference/prototype metrics.

Interpretation: 024c is a real recovery for the K/V pathway but not a style
quality win. The next move should be poetry-specific and objective-specific, not
another generic continuation. Screenplay should be treated as near solved at the
pathway level.
