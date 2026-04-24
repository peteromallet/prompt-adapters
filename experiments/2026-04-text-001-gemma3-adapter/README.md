# 2026-04-text-001-gemma3-adapter

Status: running. Results below are in progress, preliminary results from the current text adapter run.

## Question

Can a reference-conditioned prefix K/V adapter on a frozen Gemma-3-4B beat prompting for style transfer?

## Hypothesis

At 2000 steps on 971 author-paired pairs across 4 registers, the adapter will beat prompted_baseline on LLM-judge win rate.

## Method

Train a small reference-conditioned prefix K/V adapter against frozen `google/gemma-3-4b-pt` on 971 paired samples across poetry, essay, speech, and screenplay. The current training entrypoint remains in `../../../text-ip-adapter/scripts/train.py` and will be migrated after the experiment stabilizes.

## Results

| Test | Verdict | Notes |
| --- | --- | --- |
| T1 reference discrimination | PASS | Step 1500, jaccard 0.002; in progress, preliminary results. |
| T2 adapter vs prompting | PASS | Step 1500, 67% LLM-judge win rate; in progress, preliminary results. |
| T3 style carryover | WEAK | Style signal transfers weakly; in progress, preliminary results. |
| T4 memorization and reference leak | PASS | Memorization and ref-leak checks pass; in progress, preliminary results. |
| T5 loss curve | SLOW-still-improving | Loss continues improving slowly; in progress, preliminary results. |

## Learnings

The adapter works mechanically and beats prompting 2/3 on Claude judge, but style carryover is weak. Data scale is the leading suspect before changing the adapter architecture.

## Replicate

Run `./run.sh` from this experiment directory. For now it points to the live prototype under `../../../text-ip-adapter/`; code will be migrated here later.
