# 2026-05-text-039-gemma3-4b-pt-paired-completion-v5-10

## Result

This run supports the paired-completion hypothesis, but only with early stopping.

For `google/gemma-3-4b-pt`, the old instruction framing was mismatched: the model is a pretrained next-token continuation model, not an instruction follower. Exp039 changed training and eval to:

```text
A piece of writing:

{reference}

Another piece by the same writer:

{target}
```

This made the visible prompt more natural and removed much of the obvious instruction/task residue seen in earlier PT generations.

## Key Metrics

| checkpoint | adapter+prompt vs prompt-only | adapter vs swap | adapter vs no-ref | read |
|---|---:|---:|---:|---|
| step 800 | 0.583 / +0.037 | 0.167 / -0.020 | 0.417 / -0.003 | cleaner text, weak hidden-adapter signal |
| step 1200 | 0.583 / +0.050 | 0.583 / +0.043 | 0.667 / +0.142 | best checkpoint; hidden adapter adds signal |
| step 1600 | 0.333 / -0.071 | 0.333 / +0.029 | 0.333 / +0.043 | regression |
| final 2000 | 0.500 / +0.094 | 0.250 / -0.105 | 0.083 / -0.135 | overtrained; hidden adapter hurts |

Each cell is `win_rate / mean_delta`, `n=12`.

## Qualitative Read

Step 800 already looked cleaner than the old instruction-format PT run: adapter-only generations were mostly verse-like rather than "Solution" or "Student response" style contamination.

Step 1200 is the first checkpoint that looks like the architecture is doing the thing we want: the model gets useful continuation behavior from the visible reference, while the hidden adapter also beats swap and no-ref conditions.

After step 1200, the effect degrades. Step 1600 and final still produce poetry-like text, but quality is uneven and contamination returns: prose commentary, textbook fragments, and generic old-poem pastiche. Final is especially bad on `adapter_vs_no_ref` and `adapter_vs_swap`, so more training at this LR is not the answer.

## Interpretation

The root issue is not simply "needs more steps." The paired-completion format shows that the adapter can influence a PT model, but the useful region is narrow. The training recipe is currently over-powering or drifting after the adapter first finds a style-useful direction.

The batch size was 1 to fit the longer visible reference prompt. That means the generic batch contrastive loss was effectively inactive, although style triplet still ran. This likely matters: the model sees style triplet pressure but not enough true in-batch discrimination.

## Next Bet

Run a tighter paired-completion follow-up:

1. Target `1000-1300` steps, not 2000+.
2. Lower LR or add stronger regularization to reduce post-1200 drift.
3. Restore real negative pressure if possible: shorter prompt/reference, gradient accumulation with explicit negative batches, or a memory-saving path that permits batch > 1.
4. Keep checkpoint evals every 200-400 steps around the suspected peak.

Current best artifact for subjective comparison is `step_1200`.
