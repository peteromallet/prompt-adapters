# 020 Analysis Summary

Status: completed.

## Artifacts

- Training artifacts: `results/training_artifacts/`
- Pathway diagnostic: `results/pathway/`
- Sampled anti-repeat outputs: `results/sampled_antirepeat/samples.jsonl`
- Local eval report: `results/eval_report.json`

Remote RunPod pod `gaw0383lfjnq7k` was terminated after artifact download.

## Headline

Dropping speech was the right diagnostic move. The poetry+screenplay core2 run
hits the pathway gate and removes the speech-driven T4 noise, but it does not
yet prove author-level style conditioning.

## Pathway

Balanced core2 n20, final checkpoint:

| variant | cos_z | cos_K_first | cos_K_last | cos_V_first | cos_V_last | gen_J |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| swap | 0.395 | 0.506 | 0.440 | 0.495 | 0.435 | 0.074 |
| zero | 0.000 | 0.382 | -0.192 | 0.330 | -0.170 | 0.001 |
| random | -0.038 | -0.162 | -0.149 | -0.099 | -0.125 | 0.005 |
| code | -0.022 | 0.019 | -0.066 | -0.025 | -0.080 | 0.004 |

This passes the pre-registered pathway target (`cos_K_last_swap <= 0.45`) with
random/code separated. It is also roughly comparable to the best 019
poetry+screenplay mean (`0.428`) despite using a new core2 probe set.

## Register Split

`cos_K_last_swap` by register:

| register | cos_z_swap | cos_K_last_swap | gen_J_swap |
| --- | ---: | ---: | ---: |
| poetry | 0.440 | 0.633 | 0.009 |
| screenplay | 0.351 | 0.248 | 0.139 |

The aggregate pass is mostly screenplay. Poetry remains only middling and is
not solved by removing speech.

## Local Eval

Sampled anti-repeat eval:

- T1 discrimination: PASS (`mean_jaccard=0.002`)
- T3 surface carryover: WEAK (`11/20`, mean advantage approximately `0.000`)
- T4 target memorization: PASS (`0.0%`)
- T4 reference leak: PASS (`0.0%`)
- T5 loss curve: PLATEAU (`-6.6%` first-to-last quarter improvement)
- LLM judges: skipped locally; no judge key available.

## Qualitative Read

The adapter outputs are mostly real poems or screenplay fragments, not collapsed
loops. Poetry is preserved. `no_ref` and prompted baselines still drift into
instruction/web detritus, which suggests the reference path is doing real
format-control work.

Remaining problems:

- poetry author separation is weak (`cos_K_last_swap=0.633`);
- screenplay still contains artifacts such as page numbers and image dimensions
  (`640x380`, `529K`);
- surface T3 is still not decisive, and a dual-judge T2/T3b is needed before any
  C1 claim upgrade.

## Decision

020 is **partially confirmed**:

- confirmed: speech was masking a healthier core2 pathway and causing T4 noise;
- not confirmed: author-level style transfer on poetry+screenplay.

Do not widen the encoder yet. The next best bet is a targeted core2 data/eval
repair:

1. Build v3.7 core2 by stripping screenplay page/image artifacts and auditing
   poetry author pairs for near-duplicate style buckets.
2. Re-evaluate `018_step1000` and `020 final` on the repaired core2 probe before
   another training run.
3. If repaired eval still shows poetry `cos_K_last_swap > 0.60`, run a
   poetry-focused ablation with stronger within-register author negatives.
4. Keep speech out until it gets its own salutation/topic repair.
