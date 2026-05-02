# Experiment 027: v5.2 Heldout-Clean Poetry Corpus

Question: does the stricter v11/v5.2 corpus keep the strong v5.0 pathway
separation while improving qualitative probe reliability?

Inputs:

- corpus: `text-ip-adapter/data/poetry_corpus_v0_source_native_curated_candidate_v11`
- pairs: `text-ip-adapter/data/pairs_v5_2_poetry_corpus_heldout_clean`
- config: `text-ip-adapter/configs/stage1_v5_2_poetry_corpus_heldout_clean_triplet_restart006.yaml`

Compared with experiment 026, this removes high-risk OCR sources and several
heldout/probe contaminants, including bad Browning, Wordsworth, O'Reilly,
Masefield, and Maynard source buckets.

Decision rule:

- Continue this data direction if `mean_cos_K_last_swap` stays well below v4.5
  and sampled adapter generations remain poem-like with low metadata/template
  drift.
- If pathway stays strong but deterministic generations remain generic, move to
  surface-style objective/eval work rather than adding noisy scale.
