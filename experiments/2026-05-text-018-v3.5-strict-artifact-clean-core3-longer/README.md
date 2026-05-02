# Experiment 018 - v3.5 strict artifact-clean core3 longer

Status: completed. RunPod pod `1vn8vxnojn66zw` was terminated after
evaluation artifacts were downloaded.

## Question

Does continuing from the promising 017 checkpoint on stricter v3.5-cleaned data
convert register-positive, loop-free generations into stronger author-level
style conditioning?

## Why This Exists

017 was the first run in this thread to combine a healthy enough pathway with
substantially cleaner sampled generations:

- `cos_K_last_swap=0.502`, random/code near zero or negative;
- adapter `repeat3_mean=0.002`, repeated-line mean `0.0`;
- T1 PASS and T4 PASS/PASS;
- T5 SLOW, meaning the model was still improving when the short schedule ended.

The remaining gap is author-specific style, not basic pathway mechanics or loop
control.

Before launch, an n=20 probe audit found a wrapped Gutenberg picture block in
v3.4 heldout reference text. v3.5 is a narrow persisted repair over v3.4 that
removes wrapped picture/illustration/note blocks and standalone page/year
fragments, then preserves the author-disjoint split shape.

## Method

- Continue from `checkpoints/stage1_v3_4_artifact_clean_core3_smoke/final.pt`.
- Use v3.5 strict artifact-clean core3 data.
- Keep no-trunk projector and contrastive `0.1`.
- Lower LR for continuation: projector `2e-5`, encoder `1e-5`.
- Train 3,000 continuation steps.
- Evaluate with n>=20 pathway and sampled anti-repeat generation.

## Gates

- Pathway: random/code must remain near zero; swap should not collapse toward
  014-style values.
- Generation: repeat metrics must remain near zero.
- T1 and T4 must pass.
- T2/T3b require dual-judge evaluation; Haiku-only is not acceptable evidence.

## Results

Training completed and wrote `final.pt`. The run is not a clean success.

- Pathway n20: random/code stayed separated, but same-register swap separation
  worsened badly: `cos_z_swap=0.819`, `cos_K_last_swap=0.909`.
- Sampled anti-repeat generation stayed clean: adapter `repeat3_mean=0.001`,
  repeated-line mean `0.0`, heuristic artifact rows `1/20`.
- Local eval battery: T1 PASS (`mean_jaccard=0.004`), surface T3 WEAK
  (`12/20`), T4 WEAK/WEAK (`10%` target memorization and `10%` reference
  leak), T5 PLATEAU (`3.0%` improvement).
- LLM judges were skipped because no judge key was available.

Important caveat: the n20 default probe set is not comparable to 017's balanced
n15 probe. It selected mostly two authors per register and repeated the same
author pairs. I created
`text-ip-adapter/data/pairs_v3_5_artifact_clean_core3/probes_balanced_n21.jsonl`
for the next comparable pathway/eval pass.

## Decision

Do not promote the 3000-step final checkpoint. The best next move is not a
longer continuation. Re-evaluate 017 final and 018 early checkpoints on the new
balanced n21 probe, then choose an early-stop checkpoint or a shorter v3.5 run.
