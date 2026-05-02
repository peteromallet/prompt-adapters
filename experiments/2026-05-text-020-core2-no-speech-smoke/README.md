# Experiment 020 - Core2 No-Speech Smoke

Status: completed. RunPod pod `gaw0383lfjnq7k` was terminated after artifact
download.

## Question

Does removing the collapsed speech register let the adapter show cleaner
reference conditioning on poetry+screenplay?

## Why This Exists

019 showed the aggregate metric was hiding a register split:

- screenplay is strong, especially at 018 step1000 (`cos_K_last_swap=0.216`);
- poetry is middling (`0.640`);
- speech is collapsed across all checkpoints (`~0.97`).

Speech also causes T4 false positives through formulaic salutations. This run
temporarily removes speech instead of letting it dominate the aggregate.

## Method

- Dataset: `data/pairs_v3_6_core2_poetry_screenplay`.
- Registers: poetry and screenplay only.
- Init: `checkpoints/stage1_v3_5_artifact_clean_core3_longer/step_1000.pt`.
- Train 1,000 low-LR continuation steps.
- Evaluate on core2 balanced n20 probes.

## Decision Rule

Promising if:

- `cos_K_last_swap <= 0.45`;
- random/code stay near zero or negative;
- sampled anti-repeat generations remain low-repeat;
- T4 does not show non-formulaic leakage.

## Result

Partially confirmed.

020 hit the pathway target on balanced core2 n20:

- `cos_K_last_swap=0.440`;
- random/code are separated (`-0.149` / `-0.066`);
- T1 PASS, T4 PASS/PASS;
- sampled generations are low-repeat and preserve poetry/script formats.

But the register split matters: screenplay is strong
(`cos_K_last_swap=0.248`) while poetry remains middling
(`cos_K_last_swap=0.633`). Surface T3 is still only WEAK (`11/20`), so this is
not a C1 claim win yet.

See `results/analysis_summary.md`.
