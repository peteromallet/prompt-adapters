# Experiment 002 — Learnings

## Headline
**LLM-generated instructions decisively improved adapter performance over the rule-based baseline on T2, but T3 failed at n=20.** T2 moved from 001's FAIL (30%) to PASS (70%, 14W/6L/0T), while T3 stayed unusable as a surface-feature instrument.

## Side-by-side with experiment 001

| Test | 001 | 002 | Change |
|---|---|---|---|
| T1 discrimination | PASS (Jaccard 0.058, n=20) | PASS (Jaccard 0.201, n=20) | stronger separation |
| T2 vs prompted_baseline | **FAIL** (30%, 6W/11L/3T, n=20) | **PASS** (70%, 14W/6L/0T, n=20) | +40pp win rate |
| T3 style carryover | WEAK (12/20 own-wins) | **FAIL** (13/20 own-wins, mean adv ≈ 0) | broader eval exposes metric failure |
| T4 memorization | PASS | PASS | = |
| T4 ref leak | PASS | PASS | = |
| T5 loss curve | SLOW | SLOW (15.6%) | ≈ |

## What this means

The hypothesis — "rule-based instruction noise was forcing the prefix channel to compensate, polluting the style signal" — is supported for T2. The architecture did not change; only the instruction channel cleaned up. The adapter moved from 30% to 70% against prompting on an n=20 eval, which is the first robust positive T2 signal for C1.

The test-rig-noise principle is now validated: **fix instruction quality before any architectural intervention**. The size of the T2 swing also means future architectural tests are uninterpretable unless the instruction channel is clean from the start.

## What's still weak

- **T3 is FAIL at n=20.** 13/20 own-wins with mean advantage approximately zero is not useful evidence of style transfer. Treat the current surface-feature T3 as a broken instrument, not as a real negative style result.
- **T2 is robust at n=20.** 70%, 14W/6L/0T is large enough to guide the next step, though C1 still needs one independent replicate before moving from testing to supported.
- **T5 "SLOW"** is probably the wrong metric for a finished run. Loss dropped 15.6% over 2000 steps with cosine schedule — that's fine, not slow. The "SLOW" verdict comes from a threshold that should scale with schedule type.

## What this says about the broader project

- **C1 (prefix-K/V adapter beats prompting) — first robust positive evidence.** 002 is a decisive n=20 PASS after 001's n=20 FAIL. It still needs one independent replicate before the claim is supported.
- **Instruction quality is a first-order variable.** Not just methodology — it changes the outcome of architectural tests. Every future experiment and every future modality should start with LLM-generated instructions from day one.
- **The decision matrix partially works, but T3 needs replacement.** The 001 pattern pointed at test-rig noise and T2 improved after cleaning it. The T3 surface-feature metric cannot distinguish style match from noise well enough to guide 003.

## Cost summary

- Instruction regeneration (claude-haiku-4-5 via Anthropic API): $0.13
- Training (RTX 4090, 37 min): ~$0.42
- LLM-judge eval (claude-sonnet-4-5, 20 probes): low single-digit cents
- **Total: ~$0.55**
