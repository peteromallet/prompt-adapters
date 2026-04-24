# Roadmap

Active plan of what to run next, in priority order. Gates on claim status (see [STRATEGY.md](./STRATEGY.md)).

## Active project

### text-gemma3-prefix-kv

Primary claim: C1. Current evidence: experiment 001 FAILED against prompting at n=20 (30% win rate, 6W/11L/3T), while experiment 002 PASSED at n=20 after cleaning rule-based instruction noise (70% win rate, 14W/6L/0T). T3 still fails as a decision instrument and needs an LLM-judge rebuild before 003.

Process reference: use [`program/PROCESS.md`](./PROCESS.md) before planning, launching, finalizing, or writing up experiments.

**Queued experiments**, cheapest intervention first:

| # | ID | Hypothesis | Status | Cost |
|---|---|---|---|---|
| 002 | `2026-04-text-002-gemma3-llm-instructions` | Cleaner LLM-generated instructions remove test-rig noise and free the prefix channel for style signal. T3 should improve. | **complete — T2 PASS (70%, n=20), T3 FAIL** | $0.55 |
| 003 | `2026-05-text-003-gemma3-contrastive-loss` | Contrastive loss on encoder outputs directly attacks the "encoder produces similar latents per reference" failure mode. | planned | ~$0.70 |
| 004 | `2026-05-text-004-gemma3-data-scale-10x` | 10× more data across 6+ registers cleans the style signal; standard data-scaling prescription. | planned | ~$5–10 (fetching + training) |
| 005 | `2026-05-text-005-gemma3-wider-encoder` | Widen encoder bottleneck from 16→32 queries. Expand representational capacity. | planned | ~$0.70 |

**C1 decision milestone**: after 003 and 004 complete. If both improve T2 meaningfully (>60% win rate with n≥20 probes), C1 is supported. If neither does, C1 is in trouble and we reconsider architecture.

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

- **002's T2 result replicates independently at n>=20 → C1 supported.** Jump to capability tests + audio port after one independent replicate, not from 002 alone.
- **002/003/004 all fail T2 → C1 refuted at small data scale.** Either abandon or try a different injection mechanism (Flamingo) before scaling.
- **T3 surface-feature metric turns out to be uninformative regardless of training → replace with LLM-judge-based T3** (cheap to run; rebuild eval before running 003).
