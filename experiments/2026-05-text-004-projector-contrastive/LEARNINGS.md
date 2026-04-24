# Experiment 004 — Learnings

## Headline
**Contrastive loss on projector K/V outputs broke the projector collapse decisively.** Average `cos_K_first` across pathological references dropped from 003's 0.91 baseline to 0.41 — a -0.50 swing. The architecture can learn reference conditioning when the loss landscape doesn't reward a degenerate solution. Downstream T3b style-match gain is modest (45% → 55%) but capability tests look promising: 6/8 probes show monotonic α-blend interpolation. Strength-dial saturates at λ=1 (not a smooth dial).

## Headline result tables

### Pathway probe (vs experiment 003 baseline)

| Metric | 003 baseline | **004** | Change |
|---|---|---|---|
| swap-vs-own cos_K_first | 0.978 | **0.310** | **-0.67** |
| zero-prefix cos_K_first | 0.908 | **0.409** | -0.50 |
| code-prefix cos_K_first | 0.934 | **0.333** | -0.60 |
| random-prefix cos_K_first | 0.805 | **0.608** | -0.20 (marginal) |
| Encoder cos_z swap-vs-own | 0.766 | **0.401** | -0.37 (free improvement) |

### N=20 eval

| Test | 002 | **004** |
|---|---|---|
| T1 discrimination | PASS J=0.20 | PASS J=0.18 |
| T2 vs prompting | PASS 70% | PASS 60% |
| T3 surface | FAIL 13/20 | WEAK 16/20 |
| T3b LLM style match | FAIL 45% (coin flip) | WEAK 55% (4 net wins of 20) |
| T4 mem / leak | PASS / PASS | PASS / PASS |
| T5 loss curve | SLOW 15.6% | SLOW 14.6% |

### Capability tests (n=8 probes)

| Test | Result |
|---|---|
| α-blend (own vs swap interpolation) | **6/8 monotonic** — Jaccard(α=0,k) decreases as k grows in 6 of 8 probes. Endpoint Jaccard 0.000, mid-balance asymmetry 0.036. Directional positive evidence for C3. |
| strength-dial (λ=0..2 scaling) | **saturation, not smooth ramp** — Jaccard(λ=0.5,1)=0.155, Jaccard(λ=2,1)=0.243. λ=2 is *more* similar to λ=1 than λ=0.5 is, suggesting a "loud enough" threshold around λ=1. Output coherent throughout (length(λ=2)/length(λ=1) = 1.01). C4 framing needs revision. |

## What this experiment confirmed

1. **The projector is the right place to apply contrastive pressure.** Direct contrastive loss on per-layer K/V outputs broke the near-constant projector behavior. Same target couldn't have been reached by adding more data alone.

2. **The encoder benefits as a side effect.** cos_z dropped from 0.77 → 0.40 for swap. Gradient flow through the contrastive loss back-propagated through the projector and into the encoder, making it more reference-discriminative. Free improvement.

3. **The trade-off with NTL is real but tolerable.** T2 dropped from 70% to 60% — the contrastive term competes with next-token CE. That cost bought us a real K/V gap. Worth it.

4. **Architecture works mechanically as advertised.** The injection + base model are highly sensitive to small K/V variations. The earlier 002 failure was strictly the projector being a near-constant function.

5. **003 was the load-bearing diagnostic.** Without 003 localizing the bottleneck to the projector, we'd have run "contrastive on encoder outputs" — wrong layer, wouldn't have helped. Pathway probes earn their cost.

## What this experiment did NOT confirm

1. **Reference-driven style match is still weak.** T3b at 55% with n=20 has 95% CI of roughly [31%, 77%] — statistically indistinguishable from 50% coin flip. The adapter is now using the reference (cos_K/V proves it), but the use isn't strongly aligning with the style axis humans/Claude perceive.

2. **C3 (composability) — directional positive but not decisive.** 6/8 monotonic Jaccard interpolation is meaningful, but the metric is text-Jaccard, not style-axis aware. We don't yet know if α=0.5 looks STYLISTICALLY intermediate — only that it's textually positioned between α=0 and α=1.

3. **C4 (smooth strength control) — needs reframing.** Strength-dial isn't smooth. There's a "regime" effect: prefix saturates around λ=1, and λ=2 doesn't add proportionally more conditioning. This is still a useful capability (you can dial conditioning ON or OFF) but the "continuous knob" pitch needs to retreat.

4. **Marginal pass on must-criteria.** T2 = 60% exactly (the threshold), 4 net wins of 20 on T3b (threshold was 3), random-variant cos_K = 0.61 (threshold was 0.6). Three must-criteria are at the edge.

## Where the gap probably comes from

Contrastive loss rewards "K/V outputs differ across references" without prescribing HOW they should differ. The model learned to vary K/V along *some* axis, but that axis doesn't strongly align with "style" as a Claude judge perceives it. Two paths:
- **Stronger contrastive** (weight 0.3 or 0.5): may push T3b further but risks T2 regression.
- **Architectural fix** (no-trunk projector, exp 005): each per-layer head reads z directly, eliminating the shared-trunk subspace constraint.
- **Better data** (exp 006): more authors, more pairs per author. May help the style axis emerge.

## Process notes

- This was the first experiment launched via `tools/launch-experiment.sh` end-to-end. Worked cleanly.
- `finalize-experiment.sh` ran but did NOT auto-populate `experiment.yaml results:` — known gap, scoped as a script extension.
- `LEARNINGS.md` (this file), project + program rollups, and ROADMAP table updates were done MANUALLY (also script-extension TODOs).

## Cost

| Step | Cost |
|---|---|
| Training (37 min on RTX 4090) | ~$0.42 |
| n=20 eval + LLM judge | ~$0.04 |
| Pathway probe | ~$0.05 (GPU only) |
| Capability tests | ~$0.05 (GPU only) |
| **Total** | **~$0.56** |

## Decision tree for what comes next

| Outcome combination | Next experiment | Rationale |
|---|---|---|
| All capability tests strongly positive (T3b PASS too) | 006 (audio port) | C1 + C3 supported; move to cross-modality |
| Capability tests OK + T3b WEAK | 005 (stronger contrastive OR no-trunk) | Push T3b past 60% decisively before audio port |
| Capability tests fail | Reconsider architecture | Maybe Flamingo per-layer cross-attention, not prefix-K/V |

We're in row 2: **next is 005 — either stronger contrastive (weight 0.3) or architectural no-trunk fix.**
