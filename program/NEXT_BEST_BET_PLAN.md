# Next Best Bet Plan - text-gemma3-prefix-kv after 006 and v2 failures

Authored: 2026-04-25  
Parent experiment: `2026-05-text-006-projector-no-trunk`  
Claims touched: C1 (`prefix K/V beats prompting for style transfer`) and C3 (`alpha-blending produces smooth style interpolation`)  
Status: pre-registration plan for the next diagnostic branch, not an experiment result  
Supersedes: [`DATA_10X_PLAN.md`](./DATA_10X_PLAN.md) for the active v2/10x path. That document remains historical context, but the v2 dryrun, warmstart, and big-context evidence have changed the next move.

## 2026-04-25 execution addendum

The pre-registered v2 minfix path was run through its data gate and correctly
blocked. `v2_curated` survived only 58.5% overall and speech collapsed to 462
rows, below the stop threshold.

Fallback 008b was then run with `stage1_v2_bundle_lowmem.yaml` as a salvage
test after the full `stage1_v2_bundle.yaml` OOM'd. It completed 5,000 steps and
the final pathway probe produced:

- swap `mean_cos_K_first = 0.371`
- swap `mean_cos_K_last = 0.384`
- swap `mean_cos_V_first = 0.356`
- swap `mean_cos_V_last = 0.363`

This means the no-trunk warmstart plus active contrastive recipe can recover
non-collapsed K/V discrimination on the existing bundle, but the corpus remains
invalid as a clean v2 validation set.

Current next best bet: stop tuning this v2 corpus. Rebuild data before the next
canonical GPU run:

1. rebuild speech from Miller Center or another style-appropriate public-speech
   source;
2. replace global author split with per-register author split and hard held-out
   minimums;
3. preserve `source_dataset` and source lineage in pairs/manifests;
4. regenerate instructions consistently;
5. re-run corpus gates before launch.

Deeper follow-up found that the Miller Center source is repairable, not scarce:
the old parser collapsed every cached speech page to `washington` by reading the
global nav. The patched parser infers president from URL date and recovers 998
records across 42 presidents from the existing pod cache. See
[`DATA_ROOT_CAUSE_AND_REBUILD_PLAN.md`](./DATA_ROOT_CAUSE_AND_REBUILD_PLAN.md).

Next concrete experiment:
`2026-05-text-009-v3-data-rebuild-speechfix` (CPU-only data rebuild/gating).

## 2026-04-25 v3/010 addendum

Experiment `2026-05-text-010-v3-no-trunk-warmstart` completed on the repaired
v3 corpus. It is **pathway-positive but generation-quality-negative**.

Final pathway diagnostics:

- legacy n=20: `mean_cos_K_first_swap = 0.446`,
  `mean_cos_K_last_swap = 0.342`;
- v3 heldout-balanced n=20: `mean_cos_K_first_swap = 0.503`,
  `mean_cos_K_last_swap = 0.464`;
- balanced random/code remain low at the last K layer:
  random `0.105`, code `0.087`.

The legacy n=20 probe set was missing speech, so a new balanced probe was
generated with 5 essay, 5 poetry, 5 screenplay, and 5 speech probes. That
balanced probe exposed register-specific weaknesses:

- screenplay separates strongly (`cos_K_last_swap = -0.052`);
- essay is partial (`0.502`);
- poetry is partial but has elevated random/code similarity;
- speech own-vs-swap is nearly collapsed (`0.883`), probably because the
  held-out speech probe has only two presidential authors and a homogeneous
  public-address register.

Final smoke generations still show repetition and generic summary mode. This
means the next best bet is no longer "just run v3 no-trunk" and is not yet
"widen the encoder." The pathway exists. The blocker is data/eval/objective
alignment.

New next concrete experiment:
`2026-05-text-011-v3.1-data-eval-repair`.

Pre-registered intent:

1. increase held-out author diversity per register, especially speech;
2. remove or quarantine table-of-contents, index, reference-book, and generic
   summary chunks;
3. regenerate content-focused instructions after filtering;
4. make a register-balanced probe set canonical for final pathway diagnostics;
5. run a cheap short GPU smoke before any wider-encoder or scale run.

## TL;DR

- Do not launch `stage1_v2_bundle.yaml` as the next canonical experiment yet. It bundles too many changes to diagnose anything cleanly.
- First run a no-GPU v2 corpus audit and produce a frozen `v2_curated` manifest. The unresolved diagnosis is data quality before architecture or scale.
- Then run one single-axis experiment: `2026-05-text-008-v2-warmstart-minfix`.
- The single-axis change is: warm-start from 006, keep big-context `target_max=1024`, restore active contrastive loss with `batch_size=2` and `contrastive_weight=0.1`, and train only on the curated v2 splits.
- The reason this is load-bearing: `contrastive_kv_loss` is a no-op for `batch_size=1` because `loop.py` skips batches with `B < 2` and returns zero if no layer contributes.
- Hold `stage1_v2_bundle.yaml` as fallback 008b only if the single-axis minfix fails to recover pathway discrimination.

This follows the process rule in [`PROCESS.md`](./PROCESS.md): check prior learnings, choose the cheapest unresolved diagnosis, pre-register before launch, and keep n >= 20 for T2/T3 verdicts. It also follows [`STRATEGY.md`](./STRATEGY.md): test-rig and data quality come before more architecture or scale.

## Current State

The program has a real architectural win and a real quality problem.

Experiment 006 proved that removing the shared projector trunk works at the K/V pathway level. The reconciled 006 writeup reports `cos_K_first_swap = 0.221`, `cos_K_first_code = 0.364`, and no-trunk parameters down to 84M from 110M. But Opus re-judging downgraded the quality claim: T3b is 10/20, T2 is 16/20, alpha signal is 0.60 but non-monotonic, and 11/50 alpha-blend generations were mode-collapsed.

The v2 sequence did not cleanly validate the "more and cleaner data" story:

- v2 dryrun collapsed: `cos_K_first_swap = 0.988702392578125`, Opus T3b 4/20, Opus T2 5/20, mode collapse 28/50.
- v2 warmstart was reported degenerate despite starting from the 006 checkpoint.
- v2 big-context changed two things at once: it raised `target_max` to 1024 but dropped `batch_size` to 1 and set `contrastive_weight` to 0.0.
- `stage1_v2_bundle.yaml` is staged but confounded: it changes data, caps, instruction length, register mix, contrastive activity, and 006 mix-in at once.

The next best bet is to separate corpus poisoning from recipe failure.

## Evidence Summary

| Evidence | Config / source | Init | Batch | Target max | Contrastive effective? | Key numbers | Status | Confound |
|---|---|---:|---:|---:|---|---|---|---|
| 006 no-trunk | `prompt-adapters/experiments/2026-05-text-006-projector-no-trunk/LEARNINGS.md` | cold | 4 | 256 | yes, 0.1 | `cos_K_first_swap=0.221`; Opus T3b 10/20; T2 16/20; alpha signal 0.60 non-monotonic; 11/50 collapsed | partially confirmed | Good pathway, weak style quality |
| v2 dryrun | `prompt-adapters/program/v2_dryrun_verdict.json` + `stage1_gemma_no_trunk_v2_dryrun.yaml` | cold | 4 | 256 | yes, 0.1 | `cos_K_first_swap=0.988702392578125`; Opus T3b 4/20; T2 5/20; collapse 28/50 | investigate first | Cold start plus v2 quality issues |
| v2 warmstart | `text-ip-adapter/configs/stage1_gemma_no_trunk_v2_warmstart.yaml` | 006 | 4 | 256 | yes, 0.1 | User-reported degenerate generations despite numerically better `cos_K ~= 0.42` | failed smoke | Target truncation and data quality still open |
| v2 big-context | `text-ip-adapter/configs/stage1_v2_warmstart_bigctx.yaml` | 006 | 1 | 1024 | no | User-reported `cos_K_first_swap=0.929` | failed diagnostic | Big-context fix and contrastive removal moved together |
| v2 bundle | `text-ip-adapter/configs/stage1_v2_bundle.yaml` | 006 | 2 | 1024 | yes, 0.1 | Not launched in the local record | staged fallback | Bundles multiple fixes, ambiguous either way |

The big-context result is especially easy to overread. In `text-ip-adapter/src/text_ip_adapter/train/loop.py`, `contrastive_kv_loss` takes `B = K.shape[0]`, continues without contribution when `B < 2`, and returns zero when no layers contribute. Therefore a `batch_size: 1` run cannot test the contrastive anti-collapse mechanism. The big-context run tested "longer target without contrastive", not the full warm-start recipe.

## Open Questions Left By The V2 Sequence

- Q-A: Did contrastive being disabled cause big-context's incomplete recovery, or is the v2 corpus itself poisoning training?
- Q-B: Is screenplay whitespace collapse caused by bad `target_text` rows, by a malformed screenplay corpus, or by the model failing to learn screenplay formatting?
- Q-C: Are Medium-style essays and `mr_*` speech authors poisoning the register signal independently of OCR/length noise?
- Q-D: Would the 19% 006 mix-in in `stage1_v2_bundle.yaml` measure v2 capability, or mostly measure 006 capability diluted by v2 noise?
- Q-E: Should evaluation reuse the 006 probe set for comparability even though 006 found mislabels, or build fresh register-stratified probes from curated v2?

## Phase 1 - V2 Corpus Audit

This phase uses no GPU and must run before 008 is registered as an experiment.

### Inputs

Audit these pod-side or local files:

- `data/pairs_v2/train.v2_clean.jsonl`
- `data/pairs_v2/val.v2_clean.jsonl`
- `data/pairs_v2/test.v2_clean.jsonl`

If those files are pod-only, run the audit on the pod and copy back the manifest into the eventual experiment directory. If they can be pulled locally, run it in `text-ip-adapter` and commit the audit script before launch.

### Metrics

For each split and register, report:

- row count
- unique authors
- mean and p10/p50/p90 `ref_text` length
- mean and p10/p50/p90 `target_text` length
- percent with stripped target length below 100 chars
- percent with OCR score above 0.10, if score fields exist
- percent with `instruction` matching rule-generated patterns such as `Write a poem about`, `Draft an essay exploring`, `Compose a speech addressing`, or `Write a dramatic scene exploring`
- percent with suspicious stopword instructions, including `thou`, `while`, `about`, `also`, `must`, and `over`

For `essay`, additionally report:

- percent with `source_dataset` or source marker matching `medium`
- percent whose target contains non-literary web/article scaffolding:
  - URLs or markdown links
  - fenced code blocks
  - JavaScript/CSS/HTML/API markers
  - listicle headings such as `Step 1`, `How To`, `Guidelines`, or product-support language

For `speech`, additionally report:

- percent with author slug matching `^mr_`
- percent with `source_dataset=un_debate` and an `mr_*` author slug, which is internally suspect because UN debate is post-1945 while many `mr_*` examples appear to be Congressional-era material

For `screenplay`, additionally report:

- percent where stripped `target_text` length is below 100 chars
- percent where target is mostly whitespace
- percent where target lacks obvious screenplay/dialogue structure

### Curated Split Rule

Produce:

- `data/pairs_v2/train.v2_curated.jsonl`
- `data/pairs_v2/val.v2_curated.jsonl`
- `data/pairs_v2/test.v2_curated.jsonl`
- `data/pairs_v2/v2_curated_manifest.json`

The curated filter is pre-registered as this conjunction:

- drop rows where stripped `target_text` length < 100
- drop rows with OCR score > 0.10 when OCR score exists
- drop rows carrying a `short` flag
- drop `speech` rows where author slug matches `^mr_` and source indicates `un_debate`
- drop `essay` rows matching the non-literary web/code/listicle regex set
- drop `screenplay` entirely if fewer than 30% of screenplay rows survive the above filters

The manifest must include:

- exact filter rules
- before/after counts by split and register
- unique author counts before/after
- removed-row counts by reason
- a hash for each output jsonl
- the command used to generate it

### Audit Gates

- AG1, info: at least 60% of v2_clean survives curation in aggregate.
- AG2, must: at least 1500 surviving pairs in each of poetry, essay, and speech. Screenplay may be absent if it fails the 30% survival rule.
- AG3, must: author-disjoint splits still hold after curation.

If AG2 fails and any of poetry, essay, or speech falls below 1000 surviving pairs, stop the v2 thread. Do not launch 008 on a hollow corpus. The fallback becomes the older 10x cleaned corpus path from `DATA_10X_PLAN.md`, or a fresh source expansion pass.

## Phase 2 - Experiment 008: V2 Warmstart Minfix

Experiment id: `2026-05-text-008-v2-warmstart-minfix`  
Parent: `2026-05-text-006-projector-no-trunk`  
Consequence: consequential for C1 and C3  
Do not launch until Phase 1 passes AG2 and AG3.

### Question

After correcting screenplay collapse and obvious OCR/short/non-literary v2 noise, can the no-trunk warm-started recipe with contrastive loss actively firing recover 006-level pathway discrimination on a larger corpus?

### Hypothesis

If contrastive weight 0.1 actually fires with `batch_size >= 2`, and screenplay collapse plus non-literary essay/speech rows are removed, warmstart from 006 will recover `cos_K_first_swap <= 0.40` and Opus T3b >= 60%.

### Config

Create `text-ip-adapter/configs/stage1_v2_warmstart_minfix.yaml`.

Clone `text-ip-adapter/configs/stage1_v2_warmstart_bigctx.yaml`, but change only:

- `data.train_path: data/pairs_v2/train.v2_curated.jsonl`
- `data.val_path: data/pairs_v2/val.v2_curated.jsonl`
- `data.test_path: data/pairs_v2/test.v2_curated.jsonl`
- `training.output_dir: checkpoints/stage1_v2_warmstart_minfix`
- `training.batch_size: 2`
- `training.max_steps: 5000`
- `training.warmup: 200`
- `training.contrastive_weight: 0.1`
- keep `data.reference_max: 512`
- keep `data.instruction_max: 128` unless the audit proves instructions are regenerated or constant
- keep `data.target_max: 1024`
- keep `training.lr_projector: 5.0e-5`
- keep `training.lr_encoder: 2.5e-5`
- keep `training.init_from: checkpoints/stage1_gemma_no_trunk/final.pt`

Do not use `stage1_v2_bundle.yaml` for 008. It remains fallback 008b because it changes too many variables at once: reference cap, instruction cap, data filter, screenplay inclusion, OCR filtering, 006 mix-in, batch size, and contrastive.

### Evaluation

Run the standard five-test battery:

- T1 discrimination
- T2 adapter vs prompted baseline
- T3/T3b style carryover, with T3b as the load-bearing style criterion
- T4 memorization/reference leak
- T5 loss curve

Run these additional probes:

- pathway probe: cos_z, cos_K_first, cos_V_first across own/swap/zero/random/code references
- alpha-blend capability probe over alpha in `{0, 0.25, 0.5, 0.75, 1.0}`
- strength-dial probe over lambda in `{0, 0.5, 1.0, 2.0}`

Use dual judge for any LLM-judge criterion:

- Haiku for cheap continuity
- Opus or Sonnet for the controlling verdict

Haiku-only evidence is not acceptable after 006 showed Haiku over-rewards surface typography markers.

Probe count rule:

- n >= 20 for T2 and T3b verdicts
- no small-n result may be written up as final

Probe-set recommendation:

- Primary: build a fresh register-stratified n=20 probe set from curated validation rows, because 006 identified probe quality issues.
- Secondary: run a compatibility eval on the old 006 probe set as a non-gating appendix if budget allows.

### Decision Gates

All four must pass:

- DG1, must: pathway `cos_K_first_swap <= 0.40`. Baselines: 006 was 0.221; v2 dryrun was 0.988702392578125; bigctx was user-reported 0.929.
- DG2, must: Opus T3b adapter wins >= 12/20.
- DG3, must: mode-collapse rate below 10% on the 50-sample alpha-blend pool.
- DG4, must: Opus T2 adapter vs prompted baseline >= 60%.

### Kill Criteria

Any one should stop the run or force re-planning:

- Step <= 1000 intermediate pathway probe has `cos_K_first_swap > 0.85`.
- Any eval sample file shows repeated pure-whitespace generations after stripping.
- NaN loss appears for 50 consecutive logged steps.
- Data paths resolve to v2_clean instead of v2_curated.
- Any post-launch config change would invalidate the manifest.

The `proj_norm < 1.0` kill criterion from the draft plan is intentionally not kept. `proj_norm` is a weak proxy and could be misleading after warmstart; pathway cosines and sample collapse are better kill signals.

### Artifacts To Collect

Under `prompt-adapters/experiments/2026-05-text-008-v2-warmstart-minfix/`:

- `README.md` with pre-registered question, hypothesis, method, and decision rule
- `experiment.yaml`
- `config.yaml`
- `requirements.lock`
- `launch_manifest.json`
- `results/audit_v2_curated.json`
- `results/eval_report.json`
- `results/conditioning_probe_analysis.json`
- `results/capabilities_analysis.json`
- `results/samples_n20.jsonl`
- `results/judge_haiku.jsonl`
- `results/judge_opus.jsonl`
- `results/train_log.jsonl`
- `LEARNINGS.md`

Finalization and close must follow [`PROCESS.md`](./PROCESS.md): no manifest means no experiment; zero `TBD` at finalize; finalized is not closed; closed means learning captured and rolled up.

### Cost Estimate

Assuming one RTX 4090 at about $0.69/hr:

- training: roughly 130-180 minutes, about $1.50-$2.10
- eval and pathway/capability probes: about $0.20-$0.40
- dual-judge pass: budget about $0.40
- expected all-in: about $2.40

## Outcome Decision Tree

If all DG1-DG4 pass:

- C1 upgrades from `supported with caveat` to `supported`.
- C3 upgrades to `directional positive` if alpha signal is monotonic and mode collapse remains below DG3.
- Next experiment should not be another v2 cleanup run. Move to C4 long-context advantage or the first C2 audio/music port.

If DG1 passes but DG2 fails:

- The pathway is fixed but the style axis is still wrong.
- Do not keep tuning prefix-K/V loss weights.
- Promote `text-gemma3-flamingo` as the next architecture, because the base model may need per-layer cross-attention rather than prefix K/V.

If DG1 fails:

- The 006 recipe has a scale/data interaction that curation did not solve.
- Run fallback 008b with `stage1_v2_bundle.yaml` as a yes/no salvage test.
- Interpret 008b carefully: it is not diagnostic. A pass means "bundle works"; a fail means "v2 thread not worth more cheap tuning."

If both 008 and 008b fail:

- Trigger strategic rescope per [`STRATEGY.md`](./STRATEGY.md):
  - first: Flamingo-style per-layer cross-attention
  - second: 12B base model scale test
  - third: narrow C1 to context-efficient weak conditioning and retire the stronger moat claim

## Fallback 008b: Bundle Salvage Test

Use only if 008 fails DG1 or if the corpus audit reveals that minfix cannot be constructed while `stage1_v2_bundle.yaml` already exists on the pod.

Config: `text-ip-adapter/configs/stage1_v2_bundle.yaml`

Interpretation:

- It can answer whether the v2 thread is salvageable at all.
- It cannot identify which fix mattered because it bundles data filtering, larger reference cap, shorter instruction cap, dropped screenplay, tighter OCR, 006 mix-in, batch size 2, and active contrastive.

Minimum gates if run:

- `cos_K_first_swap <= 0.40`
- Opus T3b >= 12/20
- Opus T2 >= 60%
- mode collapse < 10%

## Cross-Cutting Rules

- Re-run pathway probes alongside T2/T3b. T2 alone has fired spuriously in this program.
- n >= 20 probes for any T2/T3b verdict.
- Author-disjoint splits are mandatory after any curation.
- Pre-register the hypothesis and gates before launch.
- Any v2-corpus experiment must carry the audit manifest in `results/audit_v2_curated.json`; a v2 experiment whose filter rules are not pre-registered is not an experiment.

## Documentation Updates Required When 008 Closes

Update these only after 008 is finalized and closed:

- `prompt-adapters/program/program.yaml`: update C1 evidence, project current experiment, and diagnostic finding.
- `prompt-adapters/program/ROADMAP.md`: update row 008 with closed outcome and revise next queue.
- `prompt-adapters/program/LEARNINGS.md`: add stable lesson through close rollup.
- `prompt-adapters/projects/text-gemma3-prefix-kv/LEARNINGS.md`: add project-specific lesson through close rollup.
- `prompt-adapters/program/DATA_10X_PLAN.md`: leave the supersession header in place.
- `prompt-adapters/program/SOURCE_EXPANSION_PLAN.md`: add a v2 curation addendum with the final audit rules.

## Open Questions For The Human / Pod Operator

- Are `data/pairs_v2/{train,val,test}.v2_clean.jsonl` only on the pod, or should they be pulled into this checkout?
- Is the `stage1_v2_warmstart_bigctx` checkpoint still on the pod and cheaply re-evaluable?
- Should 008's gating probe set be fresh curated-val probes, old 006 probes, or fresh probes plus old probes as a compatibility appendix?
- Is the pod-side `stage1_v2_bundle` data already built, or only the config staged?

## Open Assumptions

- The local checkout does not currently contain `text-ip-adapter/data/pairs_v2/*.jsonl`; the audit likely needs to run on the pod or after a data pull.
- The user-reported v2 warmstart and bigctx numbers are trusted as latest pod evidence until copied into experiment results.
- 006's final checkpoint is still available at `checkpoints/stage1_gemma_no_trunk/final.pt` on the pod.
- The `stage1_v2_bundle.yaml` data files may not exist locally; do not assume the bundle is immediately launchable without a pod preflight.
- Opus or Sonnet access is available for final judging; if not, any Haiku-only result must remain provisional.
- This document is not itself an experiment shell. The actual 008 shell should be created with `tools/plan-experiment.sh` only after Phase 1 passes.

## Immediate Ordered Next Steps

1. Locate v2 clean splits and run the Phase 1 audit.
2. Persist `v2_curated_manifest.json` and curated splits.
3. If AG2 and AG3 pass, create experiment shell `2026-05-text-008-v2-warmstart-minfix`.
4. Create `text-ip-adapter/configs/stage1_v2_warmstart_minfix.yaml` from the exact config diff above.
5. Pre-register 008 README and experiment YAML before launch.
6. Launch with manifest capture.
7. Run an intermediate pathway probe by step 1000 and apply kill criteria.
8. If not killed, finish training and run full n >= 20 dual-judge eval.
9. Finalize and close with rollups.
