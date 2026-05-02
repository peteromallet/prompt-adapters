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
| **006** | `2026-05-text-006-projector-no-trunk` | **Architectural fix: remove the shared MLP trunk in `PrefixProjector`; per-layer heads project z → K/V directly.** Eliminates the bottleneck structurally. The loss-only lever has been explored on both sides at this architecture (004 weight 0.1 weak; 005 weight 0.3 refuted), so architecture must change. | **closed — confirmed**| ~$0.80 |
| 007 | `2026-05-text-007-data-scale-10x` | Original 10× data branch after 006. Superseded by the v2 evidence sequence and the audit-first plan in [`NEXT_BEST_BET_PLAN.md`](./NEXT_BEST_BET_PLAN.md). | superseded — see `NEXT_BEST_BET_PLAN.md` | ~$5-10 |
| 008 | `2026-05-text-008-v2-warmstart-minfix` | Audit v2 first, then run the no-trunk 006 warmstart with curated v2, `target_max=1024`, `batch_size=2`, and active `contrastive_weight=0.1`. Tests whether v2 failures came from corpus noise plus disabled contrastive rather than the 006 recipe. | blocked by corpus gate; fallback 008b completed and pathway-positive but data-quality-negative — see `NEXT_BEST_BET_PLAN.md` | ~$2.40 |
| 009 | `2026-05-text-009-v3-data-rebuild-speechfix` | CPU-only data rebuild: fix Miller Center speech author extraction, replace warning-only global split behavior with per-register held-out gates, and produce a launchable v3 corpus before another GPU run. | data gates pass — v3 candidate ready | CPU-only |
| 010 | `2026-05-text-010-v3-no-trunk-warmstart` | Train the 006 no-trunk warmstart recipe on the v3 candidate corpus with fixed Miller speech, real poetry/screenplay/essay coverage, generic style instructions, batch>=2, and active contrastive. | **completed — pathway-positive but generation-quality-negative. Legacy n=20: `cos_K_last_swap=0.342`; v3 balanced n=20: `cos_K_last_swap=0.464`, random/code low. Final samples still repetitive. Speech own-vs-swap nearly collapsed (`cos_K_last_swap=0.883`) and poetry has elevated random/code similarity.** | ~$2 |
| 011 | `2026-05-text-011-v3.1-data-eval-repair` | Repair v3 data/eval before scale: more held-out authors per register, especially speech; remove summary/table-of-contents/reference-book chunks; regenerate content-focused instructions; make register-balanced probes canonical. | **completed — data/eval gates pass and pathway remains healthy (`cos_K_last_swap=0.446`, random=0.037, code=0.113), but generation quality still fails outside screenplay. Do not full-run.** | CPU + cheap GPU smoke |
| 012 | `2026-05-text-012-v3.2-boilerplate-objective-cleanup` | Filter transcript/reference-book/public-record boilerplate and repetition targets more aggressively; improve low-information instruction themes; rerun the 1,500-step smoke before scale/architecture. | **closed — audit found deeper source corruption; no-theme objective refuted** | CPU + interrupted cheap GPU smoke |
| 013 | `2026-05-text-013-v3.3-corrected-poetry-core3-smoke` | Correct bogus Gutenberg poetry IDs, apply audit-derived filters, exclude essay, and smoke the viable poetry/screenplay/speech corpus. | **completed — pathway-positive (`cos_K_last_swap=0.398`) but generation-quality-negative; do not full-run** | CPU + cheap GPU smoke |
| 014 | `2026-05-text-014-objective-ablation-core3` | Same corrected v3.3 core3 data, but test objective/decoding dynamics first: start with `contrastive_weight=0`, smaller smoke probes, 500-1000 steps. | **closed — REFUTED. Repetition persisted and pathway worsened (`cos_K_last_swap=0.792` vs 013's 0.398). Contrastive should stay on.** | cheap GPU smoke |
| 015 | `2026-05-text-015-decoding-repetition-diagnostic` | Hold the 013 contrastive-on checkpoint/data fixed and rerun probes with explicit anti-repetition decoding controls. Tests whether the loop failure is decoding-time before spending on another training run. | **completed — partially confirmed. Anti-repeat decoding removes mechanical loops (`repeat_3` and repeated-line rates ~0 across registers), but style quality still needs audit.** | cheap GPU eval |
| 016 | `2026-05-text-016-style-audit-after-decoding` | Judge/human audit of 015 sampled anti-repeat outputs versus 013 original and prompted baselines on the same probes. Tests whether loop-free outputs actually carry reference style. | blocked on judge key; manual audit completed, v3.4 cleanup derived | CPU/API audit |
| 017 | `2026-05-text-017-v3.4-artifact-clean-core3-smoke` | Train the 013 contrastive-on no-trunk recipe on the v3.4 artifact-clean core3 corpus; evaluate with pathway probe plus sampled anti-repeat decoding. | **next best bet / launching** | cheap GPU smoke |
| 018 | `2026-05-text-018-wider-encoder` | Widen encoder bottleneck from 16→32 queries. Lower priority — 010/011/013/014/015 say the immediate blocker is generation/objective/eval alignment, not global pathway collapse. | not yet scaffolded | ~$0.70 |

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
- **008 v2-warmstart-minfix fails its pathway gate after the v2 audit passes** → run `stage1_v2_bundle.yaml` only as fallback 008b; if both fail, pivot to Flamingo-style cross-attention or a 12B base-model scale test per [`NEXT_BEST_BET_PLAN.md`](./NEXT_BEST_BET_PLAN.md).
