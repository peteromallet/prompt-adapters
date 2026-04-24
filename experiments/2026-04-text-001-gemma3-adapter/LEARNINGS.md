# Learnings

## Headline

The first adapter run proved the prefix-K/V mechanism is alive, but the n=20 evaluation refuted the claim that it beats prompting. T1 passed, T2 failed at 30% win rate, and T3 was only weak.

## n=20 results

| Test | Verdict | Result |
|---|---|---|
| T1 discrimination | PASS | Jaccard 0.058, n=20 |
| T2 vs prompted_baseline | FAIL | 30% win rate, 6W/11L/3T, n=20 |
| T3 style carryover | WEAK | 12/20 own-wins |
| T4 memorization | PASS | No memorization failure observed |
| T4 reference leak | PASS | No reference leak failure observed |
| T5 loss curve | SLOW | Still improving slowly at schedule end |

## What changed from the early read

T2 dropped from 67% (n=4 peak) to 30% (n=20). That historical peak was useful as a smoke signal, but it was not a stable verdict. The n=4 probe count hid a clear negative result: rule-based prompting was not merely tied with the adapter, it beat it.

## What still holds

- Reference discrimination kicks in around step 600-1100. Before that window, adapter and swapped-reference outputs are too similar; after it, the adapter starts responding to the reference.
- The adapter path through Gemma-3-4B is mechanically sound. T1 PASS plus T4 PASS/PASS means the prefix channel changes outputs without obvious target memorization or reference leakage.
- The style signal is not reliable. T3 WEAK at 12/20 own-wins is not a project-level success.

## Interpretation

Small-n evaluation was misleading. The right diagnosis is not "adapter beats prompting but needs better style carryover"; it is "adapter works mechanically, but noisy rule-based instructions made the training objective worse than prompting." That makes instruction quality a first-order variable for this architecture, and it directly motivated experiment 002.
