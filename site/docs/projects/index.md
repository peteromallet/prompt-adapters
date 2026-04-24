# Projects

A **project** is a research thread with a shared hypothesis: one base model family + one architectural approach + one modality. Experiments within a project typically change a single axis at a time (data, loss, hyperparameters).

## Active projects

### [text-gemma3-prefix-kv](text-gemma3-prefix-kv.md)

Can a prefix-K/V reference adapter on a frozen Gemma-3-4B reliably beat prompting for style transfer? Experiments 001 (rule-based instructions, baseline) and 002 (LLM-generated instructions) underway.

## Conventions

Projects are tracked in each experiment's `experiment.yaml` via the `project:` field. Each experiment belongs to exactly one project. Cross-cutting concerns (e.g. `contrastive-loss`, `llm-instructions`, `data-scale-10x`) go in `tags:` — many-per-experiment.

Project slugs follow `<modality>-<base-model-family>-<architecture-family>`, e.g. `text-gemma3-prefix-kv`, `audio-musicgen-prefix-kv`, `text-gemma3-flamingo`.
