# Project Learnings: text-gemma3-prefix-kv

Cross-experiment findings for this research thread. Experiment-level findings live in each `experiments/<id>/LEARNINGS.md`. Program-level (modality-agnostic) findings go to [`program/LEARNINGS.md`](../../program/LEARNINGS.md).

Updated as experiments complete.

## What we've learned so far (as of experiment 004 finalized)

### 004 headline: contrastive loss on projector K/V broke the projector collapse decisively

cos_K/V across pathological references dropped from 003's 0.91 baseline to 0.41 average — a -0.50 swing. Encoder cos_z also improved as a free side-effect (0.77 → 0.40 for swap). The architecture CAN learn reference conditioning when given the right loss-landscape pressure; the 002 failure was confirmed as loss-landscape, not architectural fundamentals.

Quality gates passed but at the edge:
- T2 vs prompting: PASS but only 60% (down from 002's 70% — contrastive trades against NTL)
- T3b LLM-judge style match: WEAK (55%, 11W/7L/2T at n=20 — barely above coin flip)
- T1 discrimination: PASS (Jaccard 0.18, slightly tighter than 002)

**Capability tests (load-bearing for the program's "moat" claim):**
- α-blend interpolation: 6/8 probes show monotonic Jaccard interpolation across α∈{0,0.25,0.5,0.75,1.0}. Directional positive evidence for C3 (composability).
- Strength-dial: SATURATION rather than smooth ramp. λ=2 is more similar to λ=1 than λ=0.5 is. C4's framing needs to retreat from "continuous knob" to "thresholded conditioning depth."

### Updated diagnosis after 004

The decision matrix from 003 was correct: T1 PASS / T2 PASS / T3 FAIL pointed at the projector, contrastive loss on K/V outputs was the right intervention, and the projector unblock was real. But the gap from "K/V varies across references" to "K/V varies along the *style* axis specifically" remains open. The contrastive loss rewards variance without prescribing direction.

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

## Auto-rollup (2026-04-25)

- **[2026-05-text-005-stronger-contrastive](../experiments/2026-05-text-005-stronger-contrastive/) — refuted**: Hypothesis REFUTED. T3b regressed 55%->50%, LLM-judge alpha-blend signal inverted +0.25->-0.25, pathway cos_K for same-domain refs got WORSE (swap 0.31->0.69, code 0.33->0.69). T2 actually improved 60%->65%. Projector responds non-monotonically to contrastive weight; more pressure is not the answer. Next

## Auto-rollup (2026-04-25)

- **[2026-05-text-006-projector-no-trunk](../experiments/2026-05-text-006-projector-no-trunk/) — partially_confirmed**: Architectural fix works at K/V pathway (cos_K_first_swap 0.69→0.22, audit-proof). LLM-judge results initially looked like a clean PASS under Haiku (16/20 T3b, signal 1.0), but Opus cross-check showed 50% T3b, non-monotonic α-curve, 11/50 mode-collapsed generations. Haiku over-rewards surface markers. Going forward: dual-judge eval required; 7/11 collapses trace to probe-file mislabels (cross-register pairs, prose labeled as poetry).

## Auto-rollup (2026-04-25)

- **[2026-05-text-010-v3-no-trunk-warmstart](../experiments/2026-05-text-010-v3-no-trunk-warmstart/) — partially_confirmed**: The v3 corpus repair preserved pathway discrimination but did not fix generation quality. Legacy n=20 `cos_K_last_swap=0.342`; v3 balanced n=20 `cos_K_last_swap=0.464`, random/code low. Final samples still repeat and drift into generic summary mode. The new balanced probe found a real eval/data gap: speech was absent from the legacy probe and remains hard to distinguish within-register (`speech cos_K_last_swap=0.883`), while poetry has elevated random/code similarity. Next experiment is v3.1 data/eval repair before architecture changes.

## Auto-rollup (2026-04-25)

- **[2026-05-text-013-v3.3-corrected-poetry-core3-smoke](../experiments/2026-05-text-013-v3.3-corrected-poetry-core3-smoke/) — pathway-positive/generation-negative**: Correcting bogus Gutenberg poetry IDs fixed the most obvious data corruption; v3.3 core3 gates pass with poetry/screenplay/speech and two held-out authors per register. Final pathway remains healthy (`cos_K_last_swap=0.398`, random=-0.039, code=0.044), but samples still repeat phrases and sentences. The next experiment should hold data fixed and ablate objective/decoding, starting with contrastive disabled and a smaller probe set.

## Auto-rollup (2026-04-25)

- **[2026-05-text-014-objective-ablation-core3](../experiments/2026-05-text-014-objective-ablation-core3/) — refuted**: Contrastive-off is not the generation-quality fix. The 750-step smoke still repeated across registers and degraded the pathway (`cos_K_last_swap=0.792` versus 013's 0.398). Use the corrected v3.3 core3 corpus with contrastive enabled; next isolate decoding-time repetition controls on the 013 checkpoint before changing architecture or launching another full training run.

## Auto-rollup (2026-04-25)

- **[2026-05-text-015-decoding-repetition-diagnostic](../experiments/2026-05-text-015-decoding-repetition-diagnostic/) — partially_confirmed**: Anti-repetition decoding is a real fix for the obvious loop pathology when applied to the 013 checkpoint. The sampled profile (`temperature=0.8`, `top_p=0.9`, `repetition_penalty=1.12`, `no_repeat_ngram_size=3`) reduced adapter repeated-line and `repeat_3` rates to 0 across poetry/screenplay/speech. It does not yet prove style conditioning quality; next run should audit 015 sampled outputs against references and baselines.

## Auto-rollup (2026-04-26)

- **[2026-05-text-017-v3.4-artifact-clean-core3-smoke](../experiments/2026-05-text-017-v3.4-artifact-clean-core3-smoke/) — partially_confirmed**: The best current recipe is v3.4 artifact-clean core3 data, no-trunk warmstart, sampled anti-repeat decoding, and contrastive `0.1`. The smoke kept reference signal alive (`cos_K_last_swap=0.502`; random/code near zero), eliminated mechanical loops (`repeat3_mean=0.002`), and passed T1/T4. It still does not prove author-level style: surface T3 failed and judge eval was unavailable. Next run should scale this exact direction rather than testing contrastive-off or another broad bundle.

## Auto-rollup (2026-04-26)

- **[2026-05-text-018-v3.5-strict-artifact-clean-core3-longer](../experiments/2026-05-text-018-v3.5-strict-artifact-clean-core3-longer/) — inconclusive_negative**: Longer continuation is not automatically better. The 3000-step v3.5 continuation kept outputs low-repeat but worsened same-register pathway separation on the n20 default probe (`cos_K_last_swap=0.909`) and introduced WEAK T4 leak/memorization. The probe itself was flawed because default n20 over-selected two authors per register; use `probes_balanced_n21.jsonl` for the next comparison. Next action is eval-only checkpoint comparison before changing architecture.

## Auto-rollup (2026-04-26)

- **[2026-05-text-019-balanced-checkpoint-comparison](../experiments/2026-05-text-019-balanced-checkpoint-comparison/) — completed**: The best current checkpoint is `018_step1000`, not 017 final or 018 final. Balanced n21 pathway: `cos_K_last_swap=0.609`; random/code remain separated; sampled outputs stay low-repeat. Register breakdown changed the diagnosis: screenplay is strong (`0.216` at step1000), poetry is middling (`0.640`), and speech is collapsed (`0.972`). Next training should isolate poetry+screenplay core2 or repair speech, not widen the encoder yet.

## Auto-rollup (2026-04-26)

- **[2026-05-text-020-core2-no-speech-smoke](../experiments/2026-05-text-020-core2-no-speech-smoke/) — partially_confirmed**: Speech exclusion gives a clean pathway-positive core2 result (`cos_K_last_swap=0.440`, random=-0.149, code=-0.066) with T1 PASS and T4 PASS/PASS. The result is not yet author-style proof: screenplay is strong (`cos_K_last_swap=0.248`), poetry is still middling (`0.633`), and surface T3 is WEAK (`11/20`). Keep speech out for now. Next step is a targeted v3.7 core2 eval/data repair: remove screenplay page/image artifacts, audit poetry author-pair separability, and re-evaluate best checkpoints before more training.

## Auto-rollup (2026-04-26)

- **[2026-05-text-021-core2-eval-data-repair](../experiments/2026-05-text-021-core2-eval-data-repair/) — completed**: Repaired core2 eval confirms `020_final` is the best current checkpoint but not a claim win. On v3.7 repaired probes, `020_final` has `cos_K_last_swap=0.502` (poetry `0.522`, screenplay `0.483`), random/code remain separated, outputs are clean, T1/T4 pass, and surface T3 is still WEAK. The old v3.6 probe overstated screenplay strength because heldout refs were too repetitive. The project bottleneck is now eval/split design and author-style proof, not obvious collapse or repetition.

## Auto-rollup (2026-04-26)

- **[2026-05-text-022-broader-clean-split-restart](../experiments/2026-05-text-022-broader-clean-split-restart/) — partially_confirmed**: Clean-heldout v3.8 removes warmstart author contamination and strengthens the core2 pathway result (`cos_K_last_swap=0.382`; poetry `0.293`, screenplay `0.470`; random/code `0.117`/`0.014`). Sampled anti-repeat eval is T1 PASS, T4 PASS/PASS, and low-repeat. But T3 surface is still WEAK and qualitative samples often show genre/register imitation more than author-specific style. Next best bet is a focused T3b judge audit of 022 sampled/greedy outputs before spending on wider encoder or larger architecture changes.

## Auto-rollup (2026-04-26)

- **[2026-05-text-023-evalclean-probe-audit](../experiments/2026-05-text-023-evalclean-probe-audit/) — negative_informative**: Dirty v3.8 poetry references were real, but not the whole problem. v3.9 eval-clean probes (`dirty_refs=0`) made the 022 checkpoint's same-register pathway weaker: aggregate `cos_K_last_swap=0.541`, poetry `0.647`, screenplay `0.435`. Random/code stayed separated, so reference signal exists, but author-style direction is not robust. This demotes "just clean eval and judge" as the next bet; the next run should clean train references/instructions and add direct own-vs-swap style pressure.

## Auto-rollup (2026-04-26)

- **[2026-05-text-024-v4-objective-data-repair](../experiments/2026-05-text-024-v4-objective-data-repair/) — partially_confirmed**: The v4 restart from 006 is the first clean pathway recovery after 023. Continuations from 022 were weak (`0.522`/`0.535`), but 024c got aggregate `cos_K_last_swap=0.360`, with screenplay excellent (`0.161`) and random/code near zero. Poetry is still weak (`0.559`) and sampled T3 FAILs (`15/32`), so the project should split the problem: screenplay pathway is close; poetry needs targeted data/objective work and stronger style proof.

- **[2026-05-text-025-poetry-specific-style-axis](../experiments/2026-05-text-025-poetry-specific-style-axis/) — ready/blocked**: Next run is staged as strict poetry-only v4.3 from 006, not a wider encoder change. v4.3 keeps poetry only, strips title/section headings, filters stage/prose-like rows, and uses 16 generic probes. Launch is blocked by missing Hugging Face auth for `google/gemma-3-4b-pt`; token sync now supports both the HF cache token file and `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN`.
