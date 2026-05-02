# Exp036 Gemma4 E2B 10k Continuation Readout

Status: completed, pod terminated.

## Setup

- Base: `google/gemma-4-E2B`
- Data: `pairs_v5_10_poetry_llm_style_medium_strong`
- Start: exp035 final checkpoint, after 2k Gemma4 cold-start steps
- Run: 8k continuation steps, approximately 10k total exposure
- Eval checkpoints: continuation steps 2k, 4k, 6k, final/8k

## Metrics

| checkpoint | K_last swap | V_last swap | z swap | adapter_prompted vs prompt win/delta | adapter vs swap win/delta | adapter vs no_ref win/delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exp035 2k | 0.257 | 0.169 | 0.310 | 0.75 / +0.212 | 0.50 / +0.037 | 0.75 / +0.226 |
| exp036 +2k | 0.093 | 0.038 | 0.163 | 0.75 / +0.131 | 0.33 / -0.071 | 0.58 / +0.009 |
| exp036 +4k | 0.029 | 0.008 | 0.116 | 0.25 / -0.079 | 0.25 / -0.069 | 0.75 / +0.136 |
| exp036 +6k | 0.088 | 0.089 | 0.120 | 0.42 / -0.022 | 0.50 / -0.021 | 0.83 / +0.249 |
| exp036 final/+8k | 0.035 | 0.047 | 0.100 | 0.67 / +0.028 | 0.33 / -0.026 | 0.50 / +0.106 |

## Qualitative Read

Longer training reduced some assignment/meta artifacts in `adapter` and `adapter_prompted`, but it did not make style control robust.

The best-looking isolated adapter samples appear around +6k/final, but pairwise own-vs-swap stays weak or negative. The adapter can generate poem-like text, but it is not reliably binding the output to the provided reference style. Prompted baselines and no-ref remain heavily contaminated by assignment/instruction artifacts, which makes some pairwise wins over `no_ref` untrustworthy.

## Conclusion

More training alone is not the next best lever. The 10k run changed outputs, but did not produce monotonic improvement or robust own-reference style adherence. The strongest next bet is to fix the generation/eval format and training data contamination:

1. Build a stricter pair/eval set that removes assignment-like prompts and outputs.
2. Add an eval that judges reference-style match directly, not just variant-relative ngram advantage.
3. Train with the same prompt format intended for inference, especially if using `adapter_prompted`.

Recommendation: do not launch another blind longer continuation from final. Use exp035 final or exp036 +6k only as candidates if we need a checkpoint for prompt-format experiments.
