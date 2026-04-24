# Prompt Adapters

Prompt Adapters is a research monorepo for reference-conditioning adapters: small trainable modules that encode reference examples into latents and inject them into frozen base models. The program will compare this pattern across text, audio, music, and video.

## Directory Map

- `core/` - shared framework shape for encoders, projectors, injection mechanisms, training loops, evaluation, and data loading.
- `modality/` - modality-specific glue for text, audio, music, and video adapters.
- `experiments/` - versioned experiment folders with metadata, configs, results, learnings, and replication notes.
- `site/` - MkDocs Material source for the project site and GitHub Pages build.
- `tools/` - small repository utilities for creating experiments, building the site, and replication workflows.

## Related Repos

The current text prototype lives beside this repository at `../text-ip-adapter/` when referenced from the repo root.

Files inside experiment directories sit one level deeper under `experiments/<id>/`, so they refer to the same sibling repository with `../../../text-ip-adapter/`.

## GitHub Pages

The Pages workflow is configured for GitHub Actions deployment. After pushing this repository to GitHub, enable Pages -> "GitHub Actions" as the Pages source in the repository settings.
