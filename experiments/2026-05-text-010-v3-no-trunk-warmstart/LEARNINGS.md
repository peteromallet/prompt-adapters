# Learnings

Status: completed on 2026-04-25.

## Bottom line

Experiment 010 is **pathway-positive but generation-quality-negative**.

The repaired v3 corpus plus 006 no-trunk warmstart does not globally collapse
the adapter pathway. The final pathway probe shows meaningful separation from
random/code references:

| Probe | swap cos_z | swap cos_K_first | swap cos_K_last | random cos_K_last | code cos_K_last |
|---|---:|---:|---:|---:|---:|
| legacy n=20 | 0.251 | 0.446 | 0.342 | 0.187 | 0.141 |
| v3 heldout-balanced n=20 | 0.445 | 0.503 | 0.464 | 0.105 | 0.087 |

But final smoke generations remain repetitive and generic. The run does not
support moving straight to scale.

## What changed during evaluation

The legacy n=20 probe set has no speech coverage. To avoid silently skipping
the repaired Miller speech path, a new v3 heldout-balanced probe was generated:

- 5 essay
- 5 poetry
- 5 screenplay
- 5 speech
- same-register swaps for every probe

Persisted at:

```text
results/probes/probes_v3_heldout_balanced_n20.jsonl
```

The original `max_new_tokens=120` final probe was too slow under
`use_cache=False` and was terminated before writing artifacts. The persisted
pathway probes use `max_new_tokens=1`, which preserves latent/K/V cosine
diagnostics but makes `gen_jaccard` non-informative. Use
`results/training/samples.jsonl` for qualitative smoke review.

## Per-register diagnosis

Balanced probe `cos_K_last_swap` by register:

- essay: 0.502
- poetry: 0.523
- screenplay: -0.052
- speech: 0.883

Interpretation:

- screenplay is the cleanest separating register;
- essay is partially separating;
- poetry still has elevated similarity to random/code references, so the model
  may be relying on a generic literary/verse prior rather than clean
  reference-specific poetry conditioning;
- speech own-vs-swap is almost collapsed, while speech vs random/code is low,
  implying the encoder/projector can distinguish speech from non-speech but not
  the two held-out presidential speech authors used by the probe.

## Generation smoke

Final `samples.jsonl` still shows repeated generic summaries and loops. Examples
include repeated "great valour, and of great prudence, and of great humanity"
and repeated historical-summary phrasing. This remains the main blocker.

## Next best bet

Do not run the wider encoder yet. The pathway is not the immediate blocker.

Run a v3.1 data/eval repair branch:

1. increase held-out author diversity per register, especially speech;
2. remove or quarantine table-of-contents, index, summary, and reference-book
   target chunks;
3. regenerate instructions from cleaned targets with content-focused prompts;
4. build a register-balanced probe set as the default final probe;
5. run a cheap short training/eval pass before scaling or widening.
