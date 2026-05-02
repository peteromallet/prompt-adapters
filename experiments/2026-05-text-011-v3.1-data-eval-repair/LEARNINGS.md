# Learnings

Status: completed on 2026-04-25.

## Bottom line

v3.1 improved the data/eval harness but did not fix generation quality enough
to justify a full training run.

The good news:

- hard data gates now pass with two held-out authors per register;
- the canonical balanced n=20 probe covers 5 each of poetry, essay,
  screenplay, and speech;
- pathway remains healthy after the 1,500-step smoke:
  `mean_cos_K_last_swap=0.446`, random `0.037`, code `0.113`.

The bad news:

- final samples still repeat;
- speech produces `Transcript Transcript` and public-document boilerplate;
- essay can collapse into repeated words or generic public-record prose;
- poetry is not convincingly poetic and repeats simple structures;
- only screenplay shows meaningful qualitative improvement.

## What changed

`scripts/build_v3_pairs.py` now supports:

- suspicious-target filtering;
- content-style instructions;
- minimum held-out author counts per register;
- per-register train floors;
- canonical balanced probe generation.

The first strict split failed because essay train was hollowed out by assigning
the largest essay authors to held-out splits. The splitter was corrected to use
the smallest author combination that satisfies held-out gates, preserving
high-capacity authors for training.

## Next

Do not launch the full v3.1 run yet.

Next best bet is a v3.2 data/objective cleanup:

1. filter `Transcript`, `To the House`, reference-book, glossary, dictionary,
   and public-record boilerplate more aggressively;
2. add a repetition-target audit over train rows, not just heldout;
3. consider excluding speech from the next quality smoke or splitting speech
   into a separate public-address-only source;
4. improve instruction generation so prompts avoid weird low-information themes
   such as `shillin and letter`;
5. rerun the same 1,500-step smoke before any full run or architecture change.
