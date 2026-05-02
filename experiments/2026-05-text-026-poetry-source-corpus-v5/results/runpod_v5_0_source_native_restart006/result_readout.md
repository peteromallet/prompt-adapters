# Result Readout: v5.0 Source-Native Poetry Run

Status: training and eval completed; orchestration marked failed only because
the local machine ran out of disk while handling downloaded train artifacts.
The pod was terminated. Required artifacts are local:

- final checkpoint:
  `train_artifacts/tmp/stage1_v5_0_poetry_corpus_curated_triplet_restart006/final.pt`
- train log:
  `train_artifacts/tmp/stage1_v5_0_poetry_corpus_curated_triplet_restart006/train_log.jsonl`
- pathway eval:
  `eval_artifacts/tmp/exp026_v5_source_native_eval/pathway/`
- sampled eval:
  `eval_artifacts/tmp/exp026_v5_source_native_eval/sampled_rep/samples.jsonl`

## Pathway Metrics

Compared with v4.5 structural-balanced:

- v4.5 `mean_cos_K_last_swap`: 0.4340
- v5.0 `mean_cos_K_last_swap`: 0.1500
- v5.0 `mean_cos_V_last_swap`: 0.1659
- v5.0 `mean_cos_K_last_random`: 0.0265
- v5.0 `mean_cos_K_last_code`: 0.0950

This is a strong pathway-separation result. It does not look like the v2
big-context collapse failure.

## Qualitative Read

Sampled adapter generations are meaningfully more poem-like than no-reference
generations:

- adapter rows: 14/14, median 248 chars, 0 metadata/instruction regex hits,
  max repeated 3-gram count 1.
- adapter-swap rows: 14/14, median 225 chars, 0 metadata/instruction regex
  hits, max repeated 3-gram count 1.
- no-ref rows: 3 metadata/instruction hits, including classroom-style prompt
  drift.

However, deterministic pathway generations remain weak:

- own/swap frequently fall into generic nature-poem templates.
- zero/code/random variants expose the old instruction/template prior very
  clearly.
- Therefore the pathway metric is real, but generation quality is not solved.

## Interpretation

The current direction is promising, but not solved.

The clean source-native corpus improved the conditioning pathway substantially.
The remaining bottleneck looks like surface-generation alignment and residual
data quality, especially OCR/IA noise and weak/noisy heldout probes, not a
complete failure of the adapter pathway.

## Next Best Bet

Build v5.1 as a stricter data-quality pass rather than increasing scale:

- remove high-risk OCR/IA source buckets found in the spotcheck,
- remove or quarantine `wright_thomas_1810_1877` from heldout,
- add OCR character-quality gates before pair derivation,
- rebuild pairs with cleaner val/test probes,
- rerun the same 1200-step config.

Also fix evaluation hygiene:

- keep sampled eval as a primary qualitative read,
- treat deterministic pathway generations as a stress test rather than a
  surface-quality verdict,
- add a small automatic report for meta hits, repeated 3-grams, and generic
  nature-template collapse.
