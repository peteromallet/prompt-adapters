# Result Readout

Exp039 completed and the RunPod pod was terminated.

## Setup

- Base: `google/gemma-3-4b-pt`
- Data: `pairs_v5_10_poetry_llm_style_medium_strong`, 2868 train rows
- Format: paired completion
- Steps: 2000, checkpoint evals at 800, 1200, 1600, final
- Batch size: 1
- Important caveat: batch contrastive is effectively inactive at batch size 1; style triplet remains active.

Prompt scaffold:

```text
A piece of writing:

{reference}

Another piece by the same writer:
```

## Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref |
|---|---:|---:|---:|
| step 800 | 0.583 / +0.037 | 0.167 / -0.020 | 0.417 / -0.003 |
| step 1200 | 0.583 / +0.050 | 0.583 / +0.043 | 0.667 / +0.142 |
| step 1600 | 0.333 / -0.071 | 0.333 / +0.029 | 0.333 / +0.043 |
| final 2000 | 0.500 / +0.094 | 0.250 / -0.105 | 0.083 / -0.135 |

Each cell is `win_rate / mean_delta`, `n=12`.

## Read

Paired completion is a real improvement over instruction-format prompting for the pretrained Gemma3 base. Step 800 was qualitatively cleaner than the previous PT run, and step 1200 is the best checkpoint: the adapter beats both swap and no-ref, which is the evidence we needed that the hidden style vector is contributing beyond the visible reference.

The run then overtrains. Step 1600 regresses and final is bad: the hidden adapter loses hard to no-ref and swap. More steps at this LR/config are not the move.

## Recommendation

Use `step_1200` as the current best checkpoint. Next run should be paired-completion again, but shorter and gentler: target 1000-1300 steps, reduce LR or add stronger regularization, and try to restore real negative pressure despite the longer prompt, either with shorter references or a memory-saving batch/negative strategy.
