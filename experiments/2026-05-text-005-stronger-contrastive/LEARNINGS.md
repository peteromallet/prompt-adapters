# Experiment 005 — Learnings

## Headline

**Hypothesis refuted.** Bumping projector-K/V contrastive_weight from 004's 0.1 to 005's 0.3 did NOT push T3b past 60%. T3b regressed from 55% → 50%, and the LLM-judge α-blend went from monotonic positive (signal +0.25) to non-monotonic negative (signal −0.25). T2 vs prompting actually improved (60% → 65%), but reference conditioning got *worse*. **The projector's response to contrastive weight is non-monotonic; "more pressure" is not the answer.** Next experiment must be 006: architectural fix (no-trunk projector).

## Side-by-side vs 004

| Test | 004 (weight 0.1) | **005 (weight 0.3)** | Δ |
|---|---|---|---|
| T1 discrimination | PASS J=0.18 | PASS | ≈ |
| T2 vs prompting | PASS 60% (12W/6L/2T) | **PASS 65%** (13W/7L/0T) | +5pp |
| **T3b LLM-judge style** | **WEAK 55%** (11W/7L/2T) | **WEAK 50%** (10W/7L/3T) | **−5pp ✗** |
| T3 surface | WEAK 16/20 | WEAK | ≈ |
| T4 mem/leak | PASS/PASS | PASS/PASS | = |
| T5 loss curve | SLOW 14.6% | SLOW 14.0% | ≈ |
| **Pathway cos_K_first swap** | 0.310 | **0.687** | **+0.38 ✗** |
| Pathway cos_K_first zero | 0.409 | 0.257 | −0.15 ✓ |
| Pathway cos_K_first random | 0.608 | 0.023 | −0.59 ✓ |
| Pathway cos_K_first code | 0.333 | 0.687 | +0.35 ✗ |
| Pathway cos_z swap | 0.401 | 0.395 | ≈ (encoder unchanged) |
| α-blend Jaccard monotonic count | 6/8 | 6/8 | = |
| **α-blend LLM-judge signal** | **+0.25** | **−0.25** | **inverted ✗** |
| α=0 frac_own (target <0.30) | 0.50 | 0.62 | farther from target ✗ |
| α=1.0 frac_own (target >0.85) | 0.75 | 0.38 | far worse ✗ |

## What went wrong (the surprising part)

Going into the experiment, the prediction was: more contrastive pressure → tighter K/V across all reference variants → better style conditioning. The actual result is that contrastive pressure has a **non-uniform effect** depending on input similarity:

- For inputs that are encoder-distant from the typical training distribution (random tokens, zero-prefix), 005 produces *much more* differentiated K/V than 004 (cos_K 0.61 → 0.02 for random, 0.41 → 0.26 for zero).
- For inputs that are encoder-similar to typical training pairs (swap = different author, same register; code = different domain but text), 005 produces *more similar* K/V than 004 (cos_K 0.31 → 0.69 for swap; 0.33 → 0.69 for code).

In other words: at weight 0.3, the projector learned a sharp threshold function on encoder similarity. It strongly differentiates outliers and weakly differentiates "neighbors." This is **exactly the wrong shape** for style transfer between different authors of the same register, which is the operationally relevant case.

## Why the LLM-judge α-blend inverted

At 004 (weight 0.1), `frac_own` grew monotonically with α from 0.50 to 0.75. At 005 (weight 0.3), the relationship is non-monotonic and slightly *negative* — at α=0 (pure swap_z) the judge picks own-style 62% of the time; at α=1.0 (pure own_z) only 38%. This is consistent with the pathway probe: when own_z and swap_z encode similar inputs (same register, different author), the projector at weight 0.3 produces nearly-identical K/V outputs in both cases. The actual generated texts diverge (low Jaccard) but along an axis that doesn't track the reference's style — possibly tracking some other latent property that's anti-correlated with style for same-domain pairs.

## What this experiment confirmed

1. **The projector's response to contrastive weight is non-monotonic, not just "more is better."** This is a real architectural finding that wasn't obvious from 004 alone.
2. **The contrastive loss as designed (`-(off-diag cosine).clamp(min=0).mean()`) acts as a "decorrelation pressure" that interacts with encoder geometry in a non-uniform way.** Strong pressure pushes outliers far apart but flattens the in-distribution discrimination — the opposite of what we want.
3. **T2 alone keeps being a misleading proxy for the architectural goal.** 005 has BETTER T2 (65% vs 004's 60%) but WORSE reference conditioning. Confirms again that T2 must always be paired with T3b + pathway probe.

## What this rules out for next steps

- "Just bump the contrastive weight" doesn't work. Both 0.1 (weak T3b) and 0.3 (regressed T3b) are sub-optimal; there isn't a clean monotonic relationship to optimize.
- The same-architecture loss-only lever has been explored on both sides. Further hyperparameter tuning at this architecture is unlikely to be informative.

## What this implies for next steps

- **Experiment 006 must be the architectural fix (no-trunk projector).** The shared MLP trunk in `PrefixProjector` is forcing all per-layer K/V outputs through a single low-dim subspace; that subspace is what gets non-uniformly squashed by contrastive pressure. Removing the trunk lets each per-layer head specialize independently.
- Possibly worth trying: **reconstruction auxiliary loss** (force the projector output to be decodable back to z by a small inverse module). This adds a constraint that the K/V must preserve reference-specific information, not just decorrelate. Could be a separate experiment 007 or layered with 006.

## Process notes

- This was the first experiment to use the *full* lifecycle scripts properly: plan-experiment, write yaml, commit core (text-ip-adapter SHA `e36293e`), launch-experiment (manifest captured automatically), train, eval, finalize, close. The new auto-populate logic for `results:` block will be exercised on this run for the first time.
- The negative result is informative and clean. Pre-registered hypothesis with concrete must-pass thresholds made the "refuted" verdict unambiguous. Without those thresholds, "T3b dropped 5pp" could have been spun as noise; with them, the experiment's outcome is clearly an architectural learning.

## Cost

| Step | Cost |
|---|---|
| Training (37 min on 4090) | ~$0.42 |
| n=20 eval + LLM judge | ~$0.04 |
| Pathway probe | ~$0.05 |
| Capability probes | ~$0.05 |
| LLM-judge α-blend | ~$0.04 |
| **Total** | **~$0.60** |
