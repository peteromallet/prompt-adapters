# Program

The **program** is the whole research endeavor. Individual experiments live inside projects; projects live inside the program.

## Thesis

Reference conditioning via **dense latent channels** can beat prompting on style/behavior transfer, and the architectural pattern **generalizes across modalities** (text, audio, music, video).

Given a reference artifact, encode it into a small set of dense vectors, inject those vectors into a frozen base generator at multiple internal layers, and train only the encoder + projector. The base's weights never move; the adapter is a small, swappable accessory.

## Claims under test

| ID | Claim | Status | Primary project |
|---|---|---|---|
| **C1** | Prefix-K/V adapters beat prompting on style transfer | testing | `text-gemma3-prefix-kv` |
| **C2** | The architectural pattern transfers across modalities | untested | (gated on C1) |
| **C3** | α-blending two reference latents produces smooth style interpolation | untested | (gated on C1) |
| **C4** | Reference-channel advantage grows with generation length | untested | (gated on C1) |

See [Strategy](./strategy.md) for full framing and decision principles, [Learnings](./learnings.md) for cross-project findings, [Roadmap](./roadmap.md) for the active queue, and [Process](../process.md) for the experiment lifecycle runbook.

## How learnings cascade

| Layer | Lives in | Example |
|---|---|---|
| Program | `program/LEARNINGS.md` | "Instruction quality is a first-order variable across all modalities." |
| Project | `projects/<slug>/LEARNINGS.md` | "For text-gemma3-prefix-kv, discrimination phase-transitions around step 600-1100." |
| Experiment | `experiments/<id>/LEARNINGS.md` | "Exp 001 T2 failed at n=20 after the earlier n=4 smoke test proved misleading." |

Findings are written at the experiment level first. When patterns repeat across experiments in a project, they roll up to project-level. When patterns span projects, they roll up to program-level.
