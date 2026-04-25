# Roadmap

Active plan of what to run next, in priority order. Gates on claim status (see [STRATEGY.md](./STRATEGY.md)).

## Active project

### text-gemma3-prefix-kv

Primary claim: C1. Current evidence — **mixed, and more complicated than prior versions of this doc claimed**:

- Experiment 001 (rule-based instructions): FAILED vs prompting at n=20 (30% win rate).
- Experiment 002 (LLM instructions): PASSED vs prompting at n=20 (70-80% win rate).
- New LLM-judge T3b on both: FAILED (coin-flip on style match).
- Experiment 003 (conditioning-pathway diagnostic): localized the failure to **the projector** — the encoder produces reference-varying latents (cos_z 0.0-0.77 across pathological references) but the projector collapses them into near-identical K/V tensors (cos 0.77-0.98). So 002's T2 PASS was register bias, not reference conditioning. **C1 is downgraded from "first positive evidence" back toward "testing" — the operational spirit of the claim requires reference-driven style change, and we don't have that yet.**

Process reference: use [`program/PROCESS.md`](./PROCESS.md) before planning, launching, finalizing, or writing up experiments.

**Queued experiments**, revised after 003's projector-bottleneck finding:

| # | ID | Hypothesis | Status | Cost |
|---|---|---|---|---|
| 002 | `2026-04-text-002-gemma3-llm-instructions` | Cleaner LLM-generated instructions remove test-rig noise. | **closed — T2 PASS but register-bias, not reference conditioning** | $0.55 |
| 003 | `2026-04-text-003-conditioning-probe` | Localize where the conditioning signal dies in the pathway. | **finalized — projector is the bottleneck** | $0.12 |
| 004 | `2026-05-text-004-projector-contrastive` | Contrastive loss on per-layer K/V outputs. | **closed — projector unblock decisive (cos_K/V 0.91→0.41); T2 PASS 60%, T3b WEAK 55%; α-blend 6/8 monotonic; strength-dial saturates at λ=1** | $0.56 |
| 005 | `2026-05-text-005-stronger-contrastive` | Bump contrastive_weight from 0.1 to 0.3, same architecture. Cheap variation to test before architectural change. | **closed — REFUTED. T3b regressed 55%→50%; α-blend LLM-judge signal inverted +0.25→−0.25; cos_K for same-domain refs got worse (swap 0.31→0.69). T2 improved 60%→65% in isolation. Projector responds non-monotonically to contrastive weight.** | $0.60 |
| **006** | `2026-05-text-006-projector-no-trunk` | **Architectural fix: remove the shared MLP trunk in `PrefixProjector`; per-layer heads project z → K/V directly.** Eliminates the bottleneck structurally. The loss-only lever has been explored on both sides at this architecture (004 weight 0.1 weak; 005 weight 0.3 refuted), so architecture must change. | **planned (next)** | ~$0.80 |
| 007 | `2026-05-text-007-data-scale-10x` | 10× more data; still deprioritized but useful after 006 — won't fix the projector bottleneck alone. | not yet scaffolded | ~$5-10 |
| 008 | `2026-05-text-008-wider-encoder` | Widen encoder bottleneck from 16→32 queries. Lower priority — encoder already produces diverse latents per 003. | not yet scaffolded | ~$0.70 |

**C1 decision milestone**: after 006 (architectural fix) completes. The success test is **not just T2 PASS** — it must include T3b PASS (LLM-judge style-match > 60% adapter wins) AND a positive conditioning-pathway probe re-run (cos_K/V across different refs < 0.6 post-training). If both pass, C1 is supported and we move to capability tests (α-blend, strength-dial). If neither does, the architecture (prefix-K/V) may genuinely not work at this scale and we reconsider — possibly Flamingo-style per-layer cross-attention, or abandoning the thread.

## Capability tests (gated on C1)

Once C1 is supported (any text-gemma3 experiment), run these before scaling further:

- **α-blend probe**: generate with `z_mix = α·z_A + (1-α)·z_B` for α ∈ {0, 0.25, 0.5, 0.75, 1.0}. Does output smoothly interpolate? C3 gate.
- **Strength-dial probe**: scale prefix by λ ∈ {0, 0.5, 1.0, 2.0}. Smooth transition?
- **Long-context probe**: generation at 2000+ tokens. Does adapter advantage over prompting grow with length? C4 gate.

All three are small additions to the existing probe framework.

## Next project candidates (gated on C1)

Once C1 is supported:

1. **`audio-musicgen-prefix-kv`** — port the pattern to MusicGen with voice/timbre references. Tests C2. First cross-modality validation.
2. **`text-gemma3-flamingo`** — ablation: per-layer gated cross-attention (Flamingo-style) vs prefix K/V on the same data. Tests whether the specific injection mechanism matters or just the general pattern.
3. **`music-musicgen-prefix-kv`** — music style conditioning (genre, artist, era) from audio clips.
4. **`video-tbd-prefix-kv`** — base model TBD (Mochi, Wan, etc). Later.

## What would cause the roadmap to change

- **004 moves cos_K/V across refs to <0.6 AND T3b > 60%** → projector bottleneck was the issue; C1 supported; move to capability tests + audio port.
- **004 fails but 005 (architectural no-trunk) succeeds** → the shared-trunk projector design was structurally wrong; update architecture doc, then move on.
- **Both 004 and 005 fail to open the K/V cosine gap** → the next-token CE training signal is too weak to teach reference conditioning at any projector shape. Consider a reconstruction auxiliary loss (force projector outputs to be decodable back to z) or abandon prefix-K/V for Flamingo-style per-layer cross-attention.
- **004/005 succeed on K/V cosine but T3b still FAIL** → the base model's attention is saturating on content tokens and ignoring the expanded prefix signal; try heavier injection (more layers, higher projector scale) or rethink.
- **Any experiment's T2 regresses back below 50% → data or config issue, investigate before continuing.**
