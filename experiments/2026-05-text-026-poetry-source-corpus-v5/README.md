# Experiment 026: v5.0 Source-Native Poetry Corpus

Question: does the high-precision source-native v9 corpus improve poetry style
generations without reviving encoder collapse?

Inputs:

- corpus: `text-ip-adapter/data/poetry_corpus_v0_source_native_curated_candidate_v9`
- pairs: `text-ip-adapter/data/pairs_v5_0_poetry_corpus_curated`
- config: `text-ip-adapter/configs/stage1_v5_0_poetry_corpus_curated_triplet_restart006.yaml`

Decision rule:

- Promising if pathway separation remains in the v4.5 range or better and
  samples become less prose-like/placeholder-like.
- Not solved if cos_K collapses toward v2 big-context behavior or generations
  still ignore poetic form despite clean data.
