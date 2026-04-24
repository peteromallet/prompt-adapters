# Prompt Adapters

Reference-conditioning adapters that inject encoded-reference latents into **frozen** base models across text, audio, music, and video. Each experiment answers one focused question; each **project** is a coherent thread of experiments under a shared hypothesis; the **program** is the whole research endeavor.

## Thesis

Reference conditioning via dense latent channels can beat prompting on style/behavior transfer, and the architectural pattern generalizes across modalities. The base's weights never move; the adapter is a small, swappable accessory.

See [Program → Strategy](program/strategy.md) for the full framing. Active experiment status in [Roadmap](program/roadmap.md).

## Projects

A project is a research thread — one base model family + one architectural approach + one modality, evolving across multiple experiments that change a single axis at a time.

| Project | Modality | Experiments | Latest result |
|---|---|---|---|
| [`text-gemma3-prefix-kv`](projects/text-gemma3-prefix-kv.md) | text | 2 (001, 002) | 001 FAIL vs prompting (n=20); 002 PASS 70% (n=20), T3 FAIL |

## Modalities planned

- **text** — current focus (Gemma-3-4B, prefix K/V)
- **audio** — future (Whisper or similar)
- **music** — future (MusicGen or similar)
- **video** — future (TBD)

## How to read this site

- **Projects** group experiments and tell the cross-experiment story.
- **Experiments** is the full flat list, filterable by project, tag, status, and consequential.
- **Architecture** explains the shared method pattern.
- **Learnings** aggregates findings across all experiments by theme.
- **Replicate** explains how to re-run any experiment from source.
