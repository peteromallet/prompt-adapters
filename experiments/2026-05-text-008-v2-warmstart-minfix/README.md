# Experiment 008 - v2 warmstart minfix

Status: blocked by pre-flight corpus gate; fallback 008b running as salvage test

## Question

After curating the v2 corpus and restoring active contrastive loss, can the 006
no-trunk warm-start recipe recover reference-specific K/V discrimination and
Opus-judged style match?

## Hypothesis

The v2 dryrun failed because cold-start training on noisy `v2_clean` collapsed to
a near-constant prefix (`cos_K_first_swap=0.989`), while the big-context
warmstart result was confounded because it used `batch_size=1` and disabled
contrastive loss. In code, `contrastive_kv_loss` contributes only when `B >= 2`.

If obvious v2 corpus poison is removed, and the 006 checkpoint is fine-tuned with
`target_max=1024`, `batch_size=2`, and `contrastive_weight=0.1`, the model should
recover 006-level pathway discrimination while gaining better target context.

Predictions:

- `cos_K_first_swap <= 0.40`
- Opus T3b adapter wins `>= 12/20`
- Opus-flagged mode collapse `< 10%` on the alpha-blend pool
- Opus T2 adapter-vs-prompted baseline `>= 60%`

## Method

1. Run v2 curation:

   ```bash
   python /workspace/text-ip-adapter/scripts/curate_v2_pairs.py \
     --input-dir /workspace/text-ip-adapter/data/pairs_v2 \
     --output-dir /workspace/text-ip-adapter/data/pairs_v2
   ```

2. Train:

   ```bash
   cd /workspace/text-ip-adapter
   PYTHONPATH=src python scripts/train.py \
     --config configs/stage1_v2_warmstart_minfix.yaml
   ```

3. Apply early kill criteria around step 1000:

   - kill/replan if intermediate `cos_K_first_swap > 0.85`
   - kill/replan if samples show repeated pure-whitespace generations
   - kill/replan on NaN loss for 50 consecutive logged steps
   - kill/replan if data paths point to `v2_clean` instead of `v2_curated`

4. Final eval:

   - five-test battery at n >= 20
   - pathway probe across own/swap/zero/random/code
   - alpha-blend and strength-dial capability probes
   - dual judge: Haiku for continuity, Opus or Sonnet as controlling verdict

Config source:

- `text-ip-adapter/configs/stage1_v2_warmstart_minfix.yaml`

Data curation source:

- `prompt-adapters/scripts_staging/curate_v2_pairs.py`

Decision gates:

- DG1: pathway `cos_K_first_swap <= 0.40`
- DG2: Opus T3b adapter wins `>= 12/20`
- DG3: mode collapse `< 10%`
- DG4: Opus T2 `>= 60%`

## Results

Pre-flight audit ran on the pod and failed the pre-registered data gates before
this became a valid launched experiment.

- AG1 failed: aggregate survival was 0.585 (< 0.60 info gate).
- AG2 failed: speech had only 462 curated rows (< 1500 must gate and < 1000
  stop threshold).
- AG3 passed: author-disjoint split check remained clean.
- Removed rows were concentrated in two failure modes:
  - `essay_non_literary_scaffolding`: 3460 rows
  - `speech_mr_un_debate`: 2835 rows

Training briefly started before the audit result was inspected, then was killed
to honor the process gate. This is not a model result; no launch manifest was
created and no final checkpoint should be interpreted.

## Learnings

The v2 corpus is not launchable under the minfix plan. Curation removes most of
the suspicious essay and speech rows, but speech collapses to 462 examples,
which is too small for the planned 008 validation. The next move should not be
`stage1_v2_warmstart_minfix` on this curated corpus.

Per `NEXT_BEST_BET_PLAN.md`, the v2 thread should either:

- fall back to an older cleaned 10x corpus with adequate speech coverage, or
- run a fresh source expansion / instruction regeneration pass before another
  v2 training attempt.

## Replicate

This experiment is not launched until:

- `v2_curated_manifest.json` exists and is copied into `results/`
- AG2 and AG3 from `NEXT_BEST_BET_PLAN.md` pass
- launch manifest captures the actual git SHA/config/data hashes

Current state: `results/audit_v2_curated.json` exists, but AG2 failed, so the
experiment remains blocked.

## Fallback 008b

Because canonical 008 is blocked, a non-canonical salvage run was launched:

- config: `text-ip-adapter/configs/stage1_v2_bundle_lowmem.yaml`
- remote checkpoint dir:
  `/workspace/text-ip-adapter/checkpoints/stage1_v2_bundle_lowmem`
- remote log: `/workspace/text-ip-adapter/train_v2_bundle_lowmem.log`
- purpose: test whether the pathway can still train on the existing bundle at
  all, after `stage1_v2_bundle.yaml` OOM'd at 1024/1024 context.

This fallback must not be interpreted as clean evidence for v2 corpus quality.
The persisted data diagnosis is in `results/data_lineage_audit.md`.

Fallback result:

- completed 5,000 steps
- saved `/workspace/text-ip-adapter/checkpoints/stage1_v2_bundle_lowmem/final.pt`
- final pathway probe saved under `results/v2_bundle_lowmem_final_probe/`
- final summary saved as `results/v2_bundle_lowmem_final_summary.md`

Final pathway diagnostic on 20 probes:

- `mean_cos_K_first_swap = 0.371`
- `mean_cos_K_last_swap = 0.384`
- `mean_cos_V_first_swap = 0.356`
- `mean_cos_V_last_swap = 0.363`
- `mean_gen_jaccard_swap = 0.003`

Conclusion: 008b recovers non-collapsed K/V discrimination on the bundle, but
does not validate the current v2 corpus. The next canonical move is a data
rebuild: fix speech source lineage, enforce per-register held-out split
minimums, preserve source metadata, and regenerate a consistent instruction
policy before launching another GPU experiment.
