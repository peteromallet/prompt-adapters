# Strategy

## Thesis

Reference conditioning via **dense latent channels** can beat prompting on style/behavior transfer, and the architectural pattern **generalizes across modalities** (text, audio, music, video).

Concretely: given a reference artifact (a poem, a speech recording, a music clip, a video clip), encode it into a small set of dense vectors, inject those vectors into a frozen base generator at multiple internal layers, and train only the encoder + projector. The base's weights never move; the adapter is a small, swappable accessory.

## Why a separate channel at all

In image generation, modern architectures (DiTs like SD3, Flux) have moved away from separate cross-attention for text conditioning toward **concat**: treat image tokens and text tokens as one sequence and let self-attention handle everything. This is cleaner because image patches and text tokens are genuinely different modalities with no common input channel.

**In LLM-land, that move doesn't apply.** The reference and the instruction are both text; concatenating them into a single prompt is *just prompting*. It's the baseline we're trying to beat, not a competing architecture. So the entire justification for prefix-K/V injection is that a dense latent channel gives us properties prompting fundamentally cannot:

1. **Higher signal per slot** — continuous vectors carry more than one-hot tokens.
2. **Mid-layer entry point** — injection into layers 17-32 is closer to where style decisions happen than early prompt tokens.
3. **Fixed cost, reusable** — 2000-char reference becomes 16 vectors; prompt cost scales with reference length. Encode once, reuse everywhere.
4. **Composability** — `z_mix = α·z_A + (1-α)·z_B` produces continuous interpolation between references. Prompts don't blend that way.
5. **Gated strength** — scalar multiplier on the prefix gives a smooth strength dial. Prompts are binary.

If none of these advantages hold empirically, the program is reinventing prompting with extra steps. Every claim below (C1-C4) exists to test one of these advantages.

## Intellectual lineage

- **Prefix/P-tuning v2 (2021)** — proved small learned latent vectors can steer frozen LLMs without touching base weights.
- **Stable Diffusion 1/2/XL "text encoder adapters"** — same structural idea in image gen: small encoder + new cross-attention layers injecting reference (text embedding) into a frozen backbone. Retrainable to swap encoders (e.g., T5 on SD1.5).
- **IP-Adapter (Tencent, 2023)** — specifically: CLIP image embeddings injected into cross-attention of a diffusion model to condition on a *reference image*. This project is the text analog.
- **Flamingo (DeepMind, 2022)** — perceiver resampler + gated cross-attention at every few layers. Closer to a "dual-stream" modern design. Sits as our fallback architecture if prefix-K/V plateaus.

The pattern is not novel. The contributions we're testing are: (a) does it work for *text→text* (rather than text→image or image→text) at small data scale, (b) does author-paired matched-style data provide a usable training signal, (c) does the method generalize across modalities.

## Claims under test

The machine-readable version is in [`program.yaml`](../../program/program.yaml). Each claim has a primary project that gates evidence:

**C1 — Prefix-K/V adapters beat prompting on style transfer.** Primary project: `text-gemma3-prefix-kv`. This is the foundation claim; if we cannot beat prompting at reasonable data scale, the architecture is not earning its complexity and the program should reconsider direction.

**C2 — The architectural pattern transfers across modalities.** Gates on C1. Tested by porting the same pattern to audio (likely MusicGen or a Whisper-based setup) and checking whether the same recipe (frozen base, perceiver encoder, prefix injection, author-paired data) produces the same behavior.

**C3 — Composability (α-blending two reference latents) produces smooth style interpolations.** Gates on C1. The load-bearing unique capability over prompting. If this works, the program has produced something prompting literally cannot replicate.

**C4 — Reference-channel advantage grows with generation length.** Gates on C1. Prompting eats context; a dense latent channel doesn't. This should compound over long generations.

## Decision principles

- **Cheapest intervention first.** Fix test-rig noise (instruction quality, probe design, eval stability) before adding architecture (contrastive loss, Flamingo-style). Architectural complexity on top of noisy evaluation is uninterpretable.
- **Capability tests before scaling.** Before investing in 10× data or more compute, run the tests that prompting *cannot* pass — α-blending, strength-dial. If those work at current scale, the architecture is proven; scaling makes it better. If they don't work at current scale, more data won't help.
- **Author-paired matched-style data is the bedrock.** Without pair-level style consistency and author-disjoint splits, the model learns content-overlap artifacts, not style.
- **Every experiment pre-registers its question.** Experiment README is drafted with hypothesis *before* the run starts. This prevents post-hoc rationalization.
- **Experiments are immutable once complete.** Core code evolves via git SHA pinning; each experiment records the SHA it was run against.
- **LLM-as-judge from day one.** Claude haiku at ~$0.001/judgment is cheap enough to be a primary eval signal, not a luxury.

## Beating prompting is necessary but not sufficient

The minimum bar for the program to be worth doing is: the adapter beats prompting on quality. If it doesn't, prompting wins by default — it's free, instant, zero infrastructure.

But beating prompting *on quality* alone doesn't earn the architectural cost. A system that beats prompting by 10pp but costs 267M extra trainable params isn't obviously worth it over just refining the prompt. The real justification is capabilities prompting literally cannot replicate:

- **α-blending** — smooth interpolation between two references (no prompt equivalent)
- **Strength-dial** — continuous conditioning strength from 0× to 2× (prompts are binary)
- **Context efficiency** — reference doesn't eat the context window; advantage grows with generation length
- **Style-library serving** — encode a reference once, reuse across thousands of generations; prompt cost scales with every call

So the validation framework has two gates:

1. **Quality gate** (beat prompting) — C1. Without this, stop.
2. **Capability gate** (do something prompting can't) — C3, C4. This is what justifies the architecture's existence.

An experiment that passes the quality gate but fails all capability gates has built "prompting with extra steps." That's not a win. The program ships only when both gates pass.

## Evaluation framework: five tests + capability probes

Every experiment runs the five-test battery. Verdicts combine into a decision matrix that tells us what to try next:

| T1 discrim. | T2 vs prompt | T3 style | T4 leak | T5 loss | Diagnosis | Next move |
|---|---|---|---|---|---|---|
| PASS | PASS | PASS | PASS | HEALTHY | It works | Capability tests + scale |
| PASS | PASS | WEAK | PASS | any | Works, style weak | More data |
| PASS | TIE | FAIL | PASS | any | Ref read but style-blind | Contrastive loss OR widen encoder |
| PASS | FAIL | any | PASS | any | Ref read but worse than prompting | Architecture change (Flamingo?) |
| WEAK/FAIL | any | any | any | any | Encoder not reading ref | Data quality first, then capacity |
| any | any | any | FAIL | any | Content leak | Data pipeline firewall broken |

Once quality gate passes, run capability probes:
- **α-blend probe**: `z_mix = α·z_A + (1-α)·z_B` across α ∈ {0, 0.25, 0.5, 0.75, 1.0}. Does output smoothly interpolate on style surface features?
- **Strength-dial probe**: scale prefix by λ ∈ {0, 0.5, 1.0, 2.0}. Smooth transition from base behavior to saturated style?
- **Long-context probe**: adapter vs prompting at 2000+ token generations. Does adapter advantage grow with length?

All three are small extensions to the existing probe framework and cost ~$0.10 per run.

## What the program is NOT trying to prove

- We are **not** trying to build a foundation model. Base models stay frozen.
- We are **not** trying to beat fine-tuning on benchmarks. Fine-tuning wins at single-task quality; we're trading that for composability and swappability.
- We are **not** chasing scaling-law plots. This is about an architectural primitive, not parameter counts.

## What would cause us to pivot or abandon

- **C1 unsupported after 5 honest text experiments** (data scale, contrastive loss, architecture variants) → the prefix-K/V channel doesn't meaningfully beat prompting at this model scale. Either pivot to a different injection mechanism (Flamingo per-layer cross-attention) or retire the thesis.
- **C2 unsupported** (pattern doesn't transfer to audio/music/video) → the approach is text-specific; narrow the program.
- **C3 refuted** (α-blending produces garbage, not interpolation) → the latent space isn't continuous in the way we thought; the "composability" pitch is unfounded; the program becomes "context-efficient prompting" rather than "a new control primitive."

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the active plan and next experiments in priority order.
