# 2026-04-text-001-gemma3-adapter

Status: complete. Results below are the n=20 retrospective evaluation for the first text adapter run.

## Question

Can a reference-conditioned prefix K/V adapter on a frozen Gemma-3-4B beat prompting for style transfer?

## Hypothesis

At 2000 steps on 971 author-paired pairs across 4 registers, the adapter will beat prompted_baseline on LLM-judge win rate.

## Method

Train a small reference-conditioned prefix K/V adapter against frozen `google/gemma-3-4b-pt` on 971 paired samples across poetry, essay, speech, and screenplay. The current training entrypoint remains in `../../../text-ip-adapter/scripts/train.py` and will be migrated after the experiment stabilizes.

## Results

| Test | Verdict | Notes |
| --- | --- | --- |
| T1 reference discrimination | PASS | Jaccard 0.058 at n=20: the adapter produces reference-conditioned differences. |
| T2 adapter vs prompting | FAIL | 30% win rate, 6W/11L/3T at n=20. The prompted baseline beat the adapter. |
| T3 style carryover | WEAK | 12/20 own-wins. There is some directional signal, but not enough to call style transfer solved. |
| T4 memorization and reference leak | PASS / PASS | Memorization and reference-leak checks pass. |
| T5 loss curve | SLOW | Training was still improving slowly rather than clearly converged. |

## Learnings

The adapter works mechanically, but the n=20 evaluation reverses the early optimistic read: T2 fails against prompting and T3 is only weak. The important methodological lesson is that small probe counts were misleading; experiment 002 tested whether instruction quality, rather than the prefix-K/V architecture itself, caused the failure.

## Replicate

Run `./run.sh` from this experiment directory. For now it points to the live prototype under `../../../text-ip-adapter/`; code will be migrated here later.
