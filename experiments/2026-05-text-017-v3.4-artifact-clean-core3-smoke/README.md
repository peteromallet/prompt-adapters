# Experiment 017 - v3.4 artifact-clean core3 smoke

Status: completed. RunPod pod `0bt8ytgxhc97kx` was terminated after
evaluation artifacts were downloaded.

## Question

Does the artifact-clean v3.4 core3 corpus improve generation quality while
preserving the healthy contrastive-on pathway from 013?

## Why This Exists

013 fixed the major poetry source corruption and kept the pathway healthy, but
generations repeated. 014 showed contrastive-off is worse. 015 showed sampled
anti-repeat decoding removes mechanical loops, but also exposed residual corpus
artifacts: screenplay page numbers, continuation boilerplate, poetry apparatus,
and speech public-record headers.

v3.4 cleans those artifacts deterministically and re-splits after cleaning so
heldout gates remain valid.

## Data

`text-ip-adapter/data/pairs_v3_4_artifact_clean_core3`

Gate summary:

- train: poetry 2,265; screenplay 5,635; speech 919
- val: poetry 183; screenplay 50; speech 50
- test: poetry 147; screenplay 50; speech 50
- val/test: 2 heldout authors per register
- author-disjoint: pass

## Method

- Same no-trunk architecture as 013.
- Same warmstart: `checkpoints/stage1_gemma_no_trunk/final.pt`.
- Keep contrastive on: `contrastive_weight=0.1`.
- Train 1,500-step smoke.
- After training, run:
  - pathway probe on v3.4 balanced probes;
  - sampled anti-repeat checkpoint eval using
    `configs/decoding_sampled_antirepeat.yaml`.

## Decision Rule

Do not full-run unless:

- pathway stays healthy, roughly `cos_K_last_swap <= 0.5`;
- sampled anti-repeat outputs are qualitatively cleaner than 015/013;
- obvious artifact leakage does not return.

## Results

017 mostly clears the smoke gate.

- Training completed 1,500 steps from `checkpoints/stage1_gemma_no_trunk/final.pt`.
- Pathway remained healthy enough to proceed: `cos_K_last_swap=0.502`,
  `cos_z_swap=0.499`, random/code `cos_K_last` near zero or negative.
- Sampled anti-repeat generations no longer show the old loop failure:
  adapter `repeat3_mean=0.002`, repeated-line mean `0.0`, empty rows `0`.
- Local eval battery on downloaded artifacts: T1 PASS
  (`mean_jaccard=0.004`), T4 PASS/PASS (`0%` target memorization and
  `0%` reference leak), T5 SLOW (`17.5%` loss improvement).
- Surface T3 failed (`7/15`, mean advantage approximately zero), but this
  metric is already known to be unreliable here. LLM-judge T2/T3b was skipped
  because no judge key was available.

Manual read: adapter outputs now look like real poetry/screenplay/speech far
more often than the no-ref and prompted baselines, which drift into generic
school-answer prose. Residual issues remain: some screenplay page-number
artifacts, one poetry sample with numeric residue, and style imitation that is
register-correct more reliably than author-specific.

## Next

Run the longer v3.4 artifact-clean core3 job, keep contrastive on, and judge it
with n>=20 dual-judge T2/T3b plus the pathway probe. This is the best current
GPU bet; do not return to contrastive-off.
