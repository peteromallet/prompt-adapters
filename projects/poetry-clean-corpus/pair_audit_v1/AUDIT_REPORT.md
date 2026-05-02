# Pair audit v1 report

Source pair set: `text-ip-adapter/data/pairs_v5_4_poetry_corpus_probe_artifact_clean`

Audited split: `train.jsonl`

Method: 10 worker shards, each producing JSONL keep/delete/edit decisions. Workers were instructed
to delete artifact rows and same-author pairs that were stylistically incoherent enough to teach an
unstable author representation.

## Outcome

- Source train pairs: 3,859
- Kept unchanged: 3,106
- Edited: 68
- Deleted: 685
- Merged v5.6 train rows: 3,174
- v5.7 train rows after dropping post-audit authors under 25 pairs: 3,135
- v5.7 train authors: 47

Reason counts across delete/edit decisions:

- `ocr`: 440
- `metadata`: 111
- `prose`: 132
- `drama_or_dialogue`: 70
- `style_mismatch`: 37
- `foreign_language`: 2
- `non_poetry`: 2

Fully removed train authors:

- `de_vere_aubrey_1814_1902`
- `fisher_benjamin_franklin_1873_1916`
- `g_k_chesterton`
- `william_shakespeare`

Post-audit under-25 train authors removed from v5.7:

- `t_s_eliot`: 22 pairs
- `w_a_n`: 17 pairs

## Outputs

- Decisions: `prompt-adapters/projects/poetry-clean-corpus/pair_audit_v1/decisions/`
- Merge summary: `prompt-adapters/projects/poetry-clean-corpus/pair_audit_v1/merge_summary.json`
- v5.6 audited pair set: `text-ip-adapter/data/pairs_v5_6_poetry_pair_audited`
- v5.7 audited min-25 pair set: `text-ip-adapter/data/pairs_v5_7_poetry_pair_audited_min25`

## Recommendation

Use v5.7 for the next training comparison. It preserves the cleaned v5.4 heldout probes while
removing 724 weak train pairs and unstable low-count author buckets. This is a meaningful quality
move, but it is also a smaller dataset, so compare it against exp029 with the same stronger-style
objective before drawing a scale conclusion.
