# text-gemma3-prefix-kv

**Modality:** text  |  **Base model:** `google/gemma-3-4b-pt`  |  **Approach:** prefix K/V adapter (perceiver encoder → per-layer GQA-aware projector → attention-hook injection at layers 17-32)

## Hypothesis

A small reference encoder (16 perceiver queries) + a per-layer projector that injects `(P=16, num_kv_heads=4, head_dim=256)` prefix K/V tensors into the mid-to-upper attention layers of a frozen Gemma-3-4B can learn to condition generation on a reference text's style, beating the prompted baseline (`"Write in the style of: <ref>"`) while maintaining content fidelity from a separate instruction input.

The key architectural claim: reference conditioning via a dedicated latent channel is more expressive than reference conditioning via prompt concatenation, because (1) a continuous vector carries more signal per "slot" than a discrete token, (2) the channel doesn't eat the context window, and (3) the channel supports α-blending of references (`z_mix = α·z_A + (1-α)·z_B`), which prompting cannot.

## Experiments in this project

| ID | Status | Change vs prior | Headline |
|---|---|---|---|
| [001](../../experiments/2026-04-text-001-gemma3-adapter/) | complete | baseline (rule-based instructions) | Adapter mechanically works, but n=20 eval shows T2 **FAIL** vs prompting (30%, 6W/11L/3T) and T3 only **WEAK** (12/20 own-wins). |
| [002](../../experiments/2026-04-text-002-gemma3-llm-instructions/) | complete | LLM-generated content-only instructions (claude-haiku-4-5) | LLM-generated instructions made T2 **PASS** at n=20 (70%, 14W/6L/0T) after 001's FAIL, but T3 is **FAIL** under the current metric. |

## Cross-experiment evaluation

All experiments in this project use the same five-test eval battery. Results populated as experiments complete.

| Test | 001 | 002 |
|---|---|---|
| T1 discrimination (adapter vs swap-ref) | **PASS** (Jaccard 0.058, n=20) | **PASS** (Jaccard 0.201, n=20) |
| T2 vs prompted baseline (Claude judge win rate) | **FAIL** (30%, 6W/11L/3T, n=20) | **PASS** (70%, 14W/6L/0T, n=20) |
| T3 style carryover (surface features) | **WEAK** (12/20 own-wins) | **FAIL** (13/20 own-wins, mean adv ≈ 0) |
| T4 target memorization | **PASS** | **PASS** |
| T4 reference leak | **PASS** | **PASS** |
| T5 loss curve | **SLOW** | **SLOW** (15.6%) |

## What this project will have decided (end-state)

If by experiment 004 or 005 this project still can't reliably beat prompting on T2 across a wider probe set, the conclusion will be that prefix-K/V at this model scale and data budget **does not** justify its complexity — and the architectural thread either needs a fundamental change (Flamingo-style per-layer cross-attention, wider encoder) or should be retired in favor of parallel-track projects (dual-stream, LoRA-on-upper-layers).

If it does beat prompting reliably, the next moves are the capability tests that prompting cannot replicate: α-blending, strength-dial, context-efficiency-at-length.
