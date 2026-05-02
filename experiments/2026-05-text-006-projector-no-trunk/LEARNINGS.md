# Experiment 006 — no-trunk projector — LEARNINGS

## Hypothesis outcome: partially_confirmed

Architectural fix is real (numeric pathway metric passes decisively). LLM-judge results initially reported `confirmed` based on Haiku's judgments, but an Opus cross-check on the same samples found Haiku was over-rewarding surface typography markers. With Opus corrections, 2/4 must-pass criteria pass outright, 1 is mixed, 1 is WEAK/FAIL.

## Results — dual-judge reconciled

| Criterion | Haiku | Opus | Verdict |
|---|---|---|---|
| `t3b_decisive` (≥ 12/20) | 16/20 (80%) | **10/20 (50%)** | **FAIL** (Opus) / WEAK |
| `t2_holds` (≥ 60%) | 16/20 (80%) | 16/20 (80%) | **PASS** (consistent) |
| `alpha_signal_strong` (≥ 0.4, monotonic, endpoints) | signal 1.0, monotonic, endpoints | signal **0.60, NON-monotonic**, endpoints | **PARTIAL** — endpoints commit but curve is not monotonic |
| `same_domain_unblocks` (cos_K_first_swap < 0.40) | — | — (numeric) | **PASS** — 0.221 |
| no_memorization_regression | 0% / 0% | — | PASS |
| loss_balance | normal | — | PASS |

Key numeric results (judge-independent):
- cos_K_first_swap = 0.221 (vs 005's catastrophic 0.69 — huge improvement)
- cos_K_first_code = 0.364 (clean separation of out-of-domain)
- param count 84M (vs 110M with trunk — 24% reduction improved rather than hurt)
- α-blend endpoint Jaccard = 0.001 (distinct content at endpoints)
- 9/10 α-blend Jaccard curves monotonic (note: this is token-overlap monotonicity, different from the LLM-judge monotonicity which Opus marked FALSE)

## What we learned — corrected

1. **The shared MLP trunk WAS the bottleneck at the K/V pathway level.** Removing it improves numeric discriminability dramatically (cos_K_first_swap 0.22 vs 0.69). This result is robust and audit-proof.
2. **Per-layer LayerNorm + zero-init K/V heads is the right architectural primitive.** Confirmed by all three numeric probes.
3. **LLM-judge style quality is NOT a clean PASS.** The Opus re-judge flagged 11/50 α-blend generations as mode-collapsed (Russian gibberish, repeated tokens, garbled text). The Haiku judge had rewarded any Gutenberg-surface marker as "style match," inflating scores by ~30 percentage points on T3b and ~40 points on α-blend signal.
4. **Mode collapse is concentrated on bad-probe cases.** Of 11 flagged collapses, ~7 trace to probe-file quality issues:
   - probe_05: cross-register pair (Montaigne essay vs Arnold poetry — adapter can't interpolate between registers)
   - probe_07: labeled "Teasdale poetry" but ref_text is a prose passage
   - probe_08: labeled "Crane poetry" but ref is a pamphlet bibliography
   - probe_09: labeled "Arnold poetry" but ref is a lecture passage
   This implies cleaner probes (from v2 corpus) should reduce mode collapse substantially.
5. **Haiku is an unreliable style-match judge.** Going forward, dual-judge (Haiku + Opus or Sonnet) eval is required for any LLM-judge criterion.

## Caveats

- N = 20 is small. 95% binomial CI on 10/20 is [28%, 72%] — wide. The "50% adapter wins" finding could be anywhere from borderline-fail to weak-pass with high confidence.
- The probe file used (`probes_n20_llm.jsonl`) inherits quality issues from the original 1× training corpus. V2 corpus has cleaner author/register metadata.
- Haiku is what we have available without API keys. Opus judgments require the Agent tool (subscription) which is limited.

## Claims status (updated)

- **C1 (prefix K/V beats prompting for style transfer)**: `supported with caveat` — adapter cleanly beats prompted_baseline 80% either judge, but "style match" is stronger as "period-register match" than "author-specific style match"
- **C3 (composable prefix latents / α-blend)**: `testing` (NOT "supported" as Haiku suggested) — endpoints commit, but middle region is inconsistent and 20–30% of generations mode-collapse
- **C4 (continuous strength dial)**: not yet strongly tested — strength_dial numeric is OK but the generations at different lambda haven't been LLM-judged

## Next

Branch (b) of the pre-registered decision tree applies (partial confirmation). Experiment 007 should:

1. **Train on v2 corpus** (42,884 unique refs, 131× more diversity than 1× corpus). Diversity likely reduces mode collapse substantially because:
   - Probes can be stratified properly (register-matched)
   - Author-disjoint splits are larger (less chance of style-family overfitting)
   - Cleaner labels (no "Crane poetry = pamphlet list" mislabels)
2. **Dual-judge by default** — include Opus verdicts alongside Haiku in the eval pipeline.
3. **Probe diversity**: test with cross-register (essay→poetry) probes explicitly to see if mode collapse is a property of the architecture or the training data distribution.

007 is no longer "optional refinement" — it's the next required validation step. If v2 training produces Opus-T3b ≥ 60% and Opus-α-signal ≥ 0.5 with fewer mode collapses, C1+C3 upgrade to supported. If not, we need to investigate collapse remediation (different training objective? smoothness regularization on z?).
