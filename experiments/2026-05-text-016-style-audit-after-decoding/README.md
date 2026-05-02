# Experiment 016 - style audit after decoding

Status: planned.

## Question

After sampled anti-repeat decoding removes loops, do adapter outputs actually
carry reference style better than swap and prompted baselines?

## Why This Exists

015 changed only decoding and almost eliminated mechanical repetition. That
makes prior qualitative failures partly uninterpretable: they measured loop
pathology as much as style conditioning.

The next decision should be an audit, not a training run.

## Inputs

- 015 sampled anti-repeat samples:
  `../2026-05-text-015-decoding-repetition-diagnostic/results/runpod_eval/workspace/text-ip-adapter/eval_runs/2026-05-text-015-decoding-repetition-diagnostic/sampled_rep/samples.jsonl`
- Probes:
  `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/probes_balanced_n15.jsonl`
- Decoding profile:
  `text-ip-adapter/configs/decoding_sampled_antirepeat.yaml`

## Decision Rule

- If sampled anti-repeat T3b/manual style audit passes, rerun larger n=30 before
  claiming progress.
- If style remains weak, keep contrastive enabled and move to target/objective
  work:
  - strip screenplay page-number artifacts;
  - hard-filter poetry apparatus/prose prompt leakage;
  - make prompts harder to answer with instruction framing;
  - train on shorter, cleaner target windows.

LLM judge was not run during 015 because `ANTHROPIC_API_KEY` was not set
locally.
