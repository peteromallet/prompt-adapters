# Experiment 010 - v3 no-trunk warmstart

Status: completed

## Question

Does the 006 no-trunk warmstart recipe produce non-collapsed pathway
conditioning and better generation quality on the repaired v3 corpus?

## Hypothesis

The v2 failures were mainly data lineage and split-policy failures. The 008b
bundle salvage run recovered pathway signal (`mean_cos_K_first_swap=0.371`) but
was confounded by `006_anchor` train mix-in and invalid held-out screenplay.

If v3 fixes the data path, then the no-trunk 006 warmstart with active
contrastive should keep `cos_K_first_swap <= 0.40` and reduce repetition in
own/swap generations relative to zero/random/code.

## Method

Train:

```bash
cd /workspace/text-ip-adapter
PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python scripts/train.py \
  --config configs/stage1_v3_no_trunk_warmstart.yaml
```

Config:

- `text-ip-adapter/configs/stage1_v3_no_trunk_warmstart.yaml`

Data:

- `data/pairs_v3_candidate/train.jsonl`
- `data/pairs_v3_candidate/val.jsonl`
- `data/pairs_v3_candidate/test.jsonl`

Early eval as originally planned:

```bash
PYTHONPATH=src python scripts/probe_conditioning.py \
  --checkpoint checkpoints/stage1_v3_no_trunk_warmstart/final.pt \
  --config configs/stage1_v3_no_trunk_warmstart.yaml \
  --probes data/pairs/probes_n20_llm.jsonl \
  --output-dir experiments/v3_no_trunk_warmstart_final_probe \
  --n-probes 20 \
  --max-new-tokens 120
```

Decision gates:

- pathway: `mean_cos_K_first_swap <= 0.40`
- OOD separation: random/code `mean_cos_K_first <= 0.25`
- generation smoke: own/swap repetition lower than zero/random/code
- no NaN/OOM

Operational note: training-time samples use `data/pairs/probes.llm.jsonl`
(4-probe smoke) to avoid spending ~15 minutes on step-0 sampling. The final
pathway gate remains `n=20` via `probe_conditioning.py`.

Execution note: the full `max_new_tokens=120` pathway probe was too slow on
`use_cache=False` decoding and was terminated before producing artifacts. The
persisted final pathway diagnostics therefore use `max_new_tokens=1`, which is
sufficient for latent/projector K/V cosine analysis but not for generation
quality. Generation quality is judged from the training-time `samples.jsonl`.

## Results

Training completed 5,000 steps on the RunPod RTX 4090. Final checkpoint:

```text
/workspace/text-ip-adapter/checkpoints/stage1_v3_no_trunk_warmstart/final.pt
```

Persisted artifacts:

- `results/training/train_log.jsonl`
- `results/training/samples.jsonl`
- `results/probes/probes_v3_heldout_balanced_n20.jsonl`
- `results/v3_no_trunk_warmstart_pathway_legacy_n20/`
- `results/v3_no_trunk_warmstart_pathway_balanced_n20/`

Pathway summaries:

| Probe | swap cos_z | swap cos_K_first | swap cos_K_last | random cos_K_last | code cos_K_last |
|---|---:|---:|---:|---:|---:|
| legacy n=20 | 0.251 | 0.446 | 0.342 | 0.187 | 0.141 |
| v3 heldout-balanced n=20 | 0.445 | 0.503 | 0.464 | 0.105 | 0.087 |

Balanced per-register `cos_K_last_swap`:

- essay: 0.502
- poetry: 0.523
- screenplay: -0.052
- speech: 0.883

Final 4-probe smoke generations remain repetitive and generic. Examples include
repeated "great valour, and of great prudence, and of great humanity" and
repeated historical-summary loops. This is not a generation-quality pass.

## Learnings

The v3 run is pathway-positive but not quality-positive. The no-trunk warmstart
recipe still carries reference-specific signal globally: random/code references
separate cleanly, and the legacy n=20 probe is in the same broad range as the
008b salvage run. However, the repaired corpus did not by itself fix writing
quality.

The balanced probe exposed a missing-eval issue in the legacy probe set:
`data/pairs/probes_n20_llm.jsonl` contains essay/poetry/screenplay but no
speech. The added `probes_v3_heldout_balanced_n20.jsonl` covers 5 examples each
of essay, poetry, screenplay, and speech with same-register swaps.

The per-register diagnosis is uneven:

- screenplay separates strongly, probably because screenplay references are
  structurally distinctive;
- essay separates moderately;
- poetry has elevated similarity to random/code references, suggesting the
  poetry axis is not cleanly anchored;
- speech own-vs-swap is nearly collapsed, likely because held-out speech has
  only two authors and presidential public-address style is too homogeneous for
  this probe design.

Next best bet: do not scale or widen the encoder yet. First repair v3.1 data
and evaluation: more held-out authors per register, speech probes spanning
distinct eras/speakers, removal of summary/list/table-of-contents targets, and
fresh content-focused instructions. Then run a short objective/decoding-focused
experiment before returning to architecture.

## Replicate
