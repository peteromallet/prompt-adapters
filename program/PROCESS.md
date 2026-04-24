# Process — Experiment Lifecycle Runbook

## Before you start

Gate the experiment on a program claim. If it does not move C1-C4, mark it non-consequential or do not run it.

Check prior experiments, project learnings, and program learnings before choosing an intervention. Prefer the cheapest unresolved diagnosis: test-rig quality before architecture, architecture before scaling, scaling before new modality.

Confirm resources before planning: data availability, expected GPU time, judge cost, and whether the run can be reproduced from the experiment directory alone.

## Plan phase

Create the experiment shell:

```bash
tools/plan-experiment.sh <id>
```

Pre-register the question, hypothesis, method, and expected decision rule in `README.md` before launch. Decide whether the experiment is consequential. Consequential experiments should be able to move a claim, roadmap branch, or project-level belief.

## Pre-flight

Start from a clean tree unless the dirty files are explicitly part of the experiment snapshot. Lock dependencies in `requirements.lock` before launch.

Verify every `config.yaml` `data_paths` entry is reachable from the experiment directory, not from the repository root or the caller's current directory.

Run the five-minute checklist: hypothesis present, config complete, dependency lock present, data paths reachable, expected outputs named, eval probe count set, and no `TBD` in fields needed to launch.

## Launch

Launch from the repository root or any directory:

```bash
tools/launch-experiment.sh <id>
```

The launch script resolves paths relative to `experiments/<id>/`, captures git SHA, dirty state, Python version, config hash, requirements hash, data hashes, and `path_base`, then writes `launch_manifest.json`.

Use `--allow-dirty` only when the dirty files are understood and intentional, such as a newly scaffolded smoke-test experiment or local notes that are unrelated to the run. If dirty files affect code, config, data, or docs for the experiment, commit or remove them first.

## Monitor

Write logs under `results/` or another path copied back into the experiment. Monitor loss, sample quality, GPU utilization, and obvious data leakage.

Kill criteria: repeated crashes, malformed samples, missing reference conditioning, data path mismatch, judge/eval scripts reading the wrong split, or any post-launch config change that would make the manifest dishonest.

## Eval

Run the five-test battery before writing up: T1 discrimination, T2 vs prompted baseline, T3 style carryover, T4 memorization/reference leak, and T5 loss curve.

**n≥20 probes minimum — hard rule.** Smaller probe sets are smoke tests only. LLM-judge should be available from day one for T2 and should replace brittle surface-feature T3 where possible.

## Finalize

Finalize robot-captured artifacts:

```bash
tools/finalize-experiment.sh <id>
```

Finalization requires a launch manifest, non-empty results, non-empty learnings, and non-`TBD` `headline` and `next` fields. It records result hashes and flips the experiment to the complete state used by the current toolchain.

Headline discipline matters: one sentence, actual result, no hedging placeholders, no `TBD`. If the result is negative, say so directly.

## Write up

Update the experiment `README.md`, `LEARNINGS.md`, and `experiment.yaml` first. Then roll up only stable lessons into `projects/<slug>/LEARNINGS.md`, `program/program.yaml`, `program/ROADMAP.md`, and `program/LEARNINGS.md`.

Do not publish preliminary smoke-test numbers as final. Historical small-n numbers are allowed only when clearly labeled as historical context.

## Replicate

Replication starts from the manifest pin: git SHA, config hash, requirements hash, data path list, data hashes, Python version, and path base.

`tools/replicate.sh` is the future entrypoint. Until it exists, the experiment directory must still contain enough metadata for a human to replay the run without guessing paths or code revisions.

## Hard rules

- n≥20 probes are required for T2/T3 verdicts.
- `data_paths` resolve relative to experiment dir.
- Experiments are immutable after write-up; create a new experiment for changes.
- Pre-register the hypothesis before launch.
- Zero `TBD` at finalize.
- No manifest means no experiment.

## Common anti-patterns

- absolute paths in `config.yaml`.
- ship preliminary results as final.
- tune after eval and write it up as if it was pre-planned.
- no manifest = no experiment.
- n=4 is a smoke test, not an eval.
