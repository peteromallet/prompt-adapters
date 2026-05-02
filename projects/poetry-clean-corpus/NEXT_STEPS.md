# Next Steps

## Current Next Best Bet

Run the v5.0 high-precision corpus experiment.

The corpus repair phase has produced a runnable candidate:

- corpus: `text-ip-adapter/data/poetry_corpus_v0_source_native_curated_candidate_v9`
- pairs: `text-ip-adapter/data/pairs_v5_0_poetry_corpus_curated`
- config: `text-ip-adapter/configs/stage1_v5_0_poetry_corpus_curated_triplet_restart006.yaml`

This is deliberately a small decisive run, not a full scale-up. It tests whether
the cleaner source-native corpus repairs the qualitative failure mode seen in
the v2 warmstart/big-context runs.

## Launch Checklist

1. Confirm RunPod API/storage and remote checkpoint availability.
2. Sync project plus `pairs_v5_0_poetry_corpus_curated`.
3. Start detached training with the v5.0 config.
4. Persist launch metadata: pod id, remote log, pid, config, and data manifest.
5. Tail logs until either training is clearly running or a launch/config failure
   is found.

## Evaluation Checklist

After training finishes:

- download or locate the final checkpoint,
- run paired own/swap/zero/random/code probes,
- compute cos_K and collapse metrics,
- generate sample poems from heldout authors,
- manually inspect for source artifacts, prose drift, instruction ignoring,
  author-style separation, and poetry quality.

## Decision Rule

If v5.0 gives lower collapse and visibly better generations, freeze this as the
new clean-corpus baseline and broaden the source manifest with the same
source-level gates.

If v5.0 still collapses or writes degenerate poetry, do not add noisy data.
Back up to the objective/checkpoint path: warm-start choice, contrastive/triplet
balance, reference/target lengths, and heldout author split difficulty.
