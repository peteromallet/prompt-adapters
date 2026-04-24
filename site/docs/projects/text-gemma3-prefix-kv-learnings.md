# Project Learnings: text-gemma3-prefix-kv

Cross-experiment findings for this research thread. Experiment-level findings live in each `experiments/<id>/LEARNINGS.md`. Program-level (modality-agnostic) findings go to [`program/LEARNINGS.md`](../../program/LEARNINGS.md).

Updated as experiments complete.

## What we've learned so far (as of experiment 002 complete)

### 002 headline: instruction quality matters a lot
Cleaner LLM-generated instructions (exp 002) moved T2 from 001's FAIL (30% win rate, 6W/11L/3T, n=20) to PASS (70% win rate, 14W/6L/0T, n=20). Architecture did not change; only the instruction channel did. **C1 has first robust positive T2 evidence, but still needs an independent replicate before it is supported.**

### Adapter mechanism is reliably alive
Across both experiments on 971 pairs, T1 discrimination is PASS (Jaccard ≈ 0) and T4 leak/memorization is PASS (0%). The prefix-K/V path through Gemma-3-4B attention is mechanically sound and the three-layer leak firewall works.

### Decision matrix diagnosis is updated
Experiment 001 landed in the "T1 PASS / T2 FAIL / T3 WEAK" quadrant at n=20, which points to noisy instructions and an underpowered or misleading style metric. Cleaning instruction quality in experiment 002 produced the predicted T2 improvement, but T3 still failed. Use the matrix for T1/T2 decisions, and rebuild T3 before it gates 003.

## What we've learned so far (retained from pre-002)

- **The adapter mechanism is alive.** T1 discrimination PASS at step 2000 — adapter produces different outputs per reference. The prefix K/V path through the frozen Gemma-3-4B attention stack is mechanically correct.
- **Discrimination has a sharp phase transition around step 600-1100.** Before step 600, adapter_swap ≈ adapter; after step 1100, they diverge cleanly. Worth watching in every future run here to confirm it's not a data-specific artifact.
- **T2 (vs prompted_baseline) must be evaluated at n>=20.** 001's historical n=4 peak was misleading; the n=20 verdict is FAIL at 30%. 002's n=20 verdict is PASS at 70% (14W/6L/0T), the first robust positive T2 evidence.
- **T3 style-carryover is unresolved and the current instrument is suspect.** 001 was WEAK at 12/20 own-wins; 002 was FAIL at 13/20 own-wins with mean advantage approximately zero. Candidate diagnoses:
  1. Surface-feature T3 cannot distinguish style match from noise and should be replaced with an LLM-judge style-match test.
  2. Encoder bottleneck is too narrow at 16 queries and underspecifies style (experiment 005).
  3. Data is too small; 971 pairs may be 10x too few (experiment 004).
- **No content leak, no target memorization.** T4 both PASS. The three-layer firewall (paragraph MinHash, target-only instructions, 5-gram reject) is working.
- **Loss curve is SLOW throughout training** (14.8% drop over 2000 steps). Cosine schedule pulls LR to ~0 by end, but model didn't plateau from convergence — it ran out of learning rate. Longer schedule + more steps probably helps *if* data is bigger; on current data, more steps likely overfit.

## Architectural choices held up

- GQA-aware projector shape `(P, 4, 256)` for Gemma-3-4B — required reading `config.num_key_value_heads` at runtime.
- Prefix K not RoPE-rotated; content K rotated as normal; prepend after `apply_rotary_pos_emb`.
- Zero-init projector output heads — training starts as a no-op, confirmed by step-0 samples.
- Injection range `[17, 32]` (inclusive) = 16 layers = `[N/2, N-2]` with N=34. No reason yet to change.

## Surprises / fragilities

- `Gemma3ForConditionalGeneration` (multimodal wrapper) is what `AutoModelForCausalLM` returns for `google/gemma-3-4b-pt`. Text tower nested at `.model.language_model.layers`. 400 MB of vision weights loaded-but-unused.
- `use_cache=True` breaks during `.generate()` with prefix injection — attention mask size mismatch on decode steps. Pragmatic workaround `use_cache=False` is slow but correct. Proper fix is deferred.
- LLM-instruction regen cost was ~$0.13 for 1159 pairs via `claude-haiku-4-5` — cheaper than estimated.

## Evaluation methodology caveat

n=4 was too noisy. Minimum n=20 from experiment 003 forward for T2 and T3 verdicts; smaller probe sets are smoke tests only and must not be written up as final results.

## Open questions for this project

1. Does cleaner instructions (002) push T3 from FAIL to at least WEAK? **Answering now.**
2. Does contrastive loss (003) resolve T3 even if 002 doesn't? Tests the encoder-bottleneck diagnosis.
3. Does 10× data (004) resolve T3 even if 002/003 don't? Tests the data-scale diagnosis.
4. After all of the above, can the adapter reliably beat prompted baseline at n≥20 probes? If not, C1 is in serious trouble.
5. Does the latent space support α-blending? Untested; will run once C1 is supported.

## Cross-experiment eval table

Populated as experiments complete. See project page [`text-gemma3-prefix-kv.md`](../../site/docs/projects/text-gemma3-prefix-kv.md) for the rendered version with links.
