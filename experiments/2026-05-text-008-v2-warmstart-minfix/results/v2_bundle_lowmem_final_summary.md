# Fallback 008b - v2 bundle low-memory final summary

Generated: 2026-04-25.

## Run

This is not canonical experiment 008. Canonical 008 was blocked by the
pre-flight v2 curation gate. This run is fallback 008b: a cheap salvage test of
the existing bundle data after `stage1_v2_bundle.yaml` OOM'd at 1024/1024
context.

- config: `text-ip-adapter/configs/stage1_v2_bundle_lowmem.yaml`
- remote checkpoint: `/workspace/text-ip-adapter/checkpoints/stage1_v2_bundle_lowmem/final.pt`
- remote probe output: `/workspace/text-ip-adapter/experiments/v2_bundle_lowmem_final_probe`
- local artifacts:
  - `results/v2_bundle_lowmem_training/train_log.jsonl`
  - `results/v2_bundle_lowmem_training/samples.jsonl`
  - `results/v2_bundle_lowmem_final_probe/analysis.json`
  - `results/v2_bundle_lowmem_final_probe/cosines.json`
  - `results/v2_bundle_lowmem_final_probe/generations.jsonl`
  - `results/v2_bundle_lowmem_final_probe/prefix_kv_summary.json`

Training completed 5,000 steps and saved `final.pt`.

## Pathway probe

Final `probe_conditioning.py` on 20 probes:

| variant vs own | cos_z | cos_K_1 | cos_K_N | cos_V_1 | cos_V_N | gen_J |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| swap | 0.271 | 0.371 | 0.384 | 0.356 | 0.363 | 0.003 |
| zero | 0.000 | 0.444 | -0.309 | 0.367 | -0.280 | 0.003 |
| random | 0.072 | 0.154 | 0.172 | 0.102 | 0.121 | 0.005 |
| code | 0.039 | 0.007 | 0.001 | -0.018 | 0.001 | 0.004 |

Interpretation:

- The pathway is no longer collapsed like v2 dryrun (`cos_K_first_swap=0.989`)
  or bigctx (`cos_K_first_swap=0.929`).
- It is weaker than 006 (`cos_K_first_swap=0.221`) but directionally successful
  as a salvage test.
- The adapter still reaches generation: `gen_J` is near zero across variants,
  meaning generations differ substantially across conditions.

## Generation quality smoke

The final probe produced 100 generations: 20 probes x own/swap/zero/random/code.

Simple repetition scan:

- own: 4/20 had a sentence repeated at least 3 times
- swap: 2/20 repeated
- zero: 13/20 repeated
- random: 13/20 repeated
- code: 11/20 repeated

This is consistent with the pathway result: real reference-specific signal is
present, but OOD/no-reference conditions still collapse into repetitive generic
text. Own/swap generations are better than zero/random/code, but this is not yet
style-match evidence. It needs a judge eval if we care about user-visible style.

## Decision

008b gives a useful answer: the no-trunk warmstart recipe plus active
contrastive can recover K/V discrimination on the bundle, even with the
low-memory 512/512 context cap.

It does not rescue v2 as a clean corpus:

- v2 speech lineage is wrong for the intended style task.
- v2 bundle held-out splits omit screenplay.
- bundle instructions are generic and confounded with the data mix.

Next best bet: stop tuning this v2 corpus. Rebuild the data path before the next
canonical training run.

Required next data work:

1. Rebuild speech from Miller Center or another style-appropriate public-speech
   source; do not label congressional floor fragments as the speech register
   for this objective.
2. Replace the global author split with per-register author splitting plus hard
   held-out minimums.
3. Preserve `source_dataset` in every pair and manifest.
4. Build a consistent instruction policy instead of mixing rule-generated
   topical prompts and generic style prompts.
5. Re-run corpus gates before any new GPU training.

