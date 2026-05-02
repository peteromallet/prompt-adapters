# Val/Test Audit After Manual Review

Question: why do val/test still have hundreds of rows?

Answer: they are not hundreds of independent conditioning examples. They are
mostly one or two repeated `ref_text` passages per author paired with many
distinct target passages.

## v4.4 Candidate Counts

Dataset: `text-ip-adapter/data/pairs_v4_4_poetry_manual`

- train: `1268`
- val: `348`
- test: `339`
- probes: `15`

## Val Structure

Val rows: `348`

Authors:

- `edna_millay`: `95`
- `edwin_arlington_robinson`: `84`
- `john_masefield`: `87`
- `matthew_arnold`: `82`

Reference docs:

- total unique `ref_doc_id`: `7`
- `edna_millay`: 2 ref docs for 95 rows
- `edwin_arlington_robinson`: 2 ref docs for 84 rows
- `john_masefield`: 2 ref docs for 87 rows
- `matthew_arnold`: 1 ref doc for 82 rows

Target docs:

- unique `target_doc_id`: `250`
- top target duplicates are only `2x`

Interpretation: val is mostly target diversity under a tiny number of repeated
conditioning references.

## Test Structure

Test rows: `339`

Authors:

- `christina_rossetti`: `100`
- `emily_dickinson`: `85`
- `sara_teasdale`: `81`
- `stephen_crane`: `73`

Reference docs:

- total unique `ref_doc_id`: `6`
- `christina_rossetti`: 1 ref doc for 100 rows
- `emily_dickinson`: 1 ref doc for 85 rows
- `sara_teasdale`: 2 ref docs for 81 rows
- `stephen_crane`: 2 ref docs for 73 rows

Target docs:

- unique `target_doc_id`: `339`
- no repeated target docs after manual cleanup

Interpretation: test is target-diverse but conditioning-reference-poor.

## Implication

The large val/test row counts are not inherently bad for language-model loss,
but they should not be interpreted as hundreds of independent style-conditioning
probes. For C1/style evaluation, the effective conditioning diversity is closer
to:

- val: 7 reference contexts
- test: 6 reference contexts
- probes: 15 curated probe rows

## Recommendation

Keep the full val/test splits if the training loop uses them for loss-style
monitoring, but use a smaller, explicitly balanced eval/probe file for style
claims.

Before the next training run, build a compact manual eval set:

- 2-4 reference docs per heldout author where possible.
- 4-8 target docs per author.
- no repeated exact `ref_text` more than a few times.
- pristine `reference_text`, `expected_target`, and `swap_reference_text`.

For training data, the bigger issue is not val/test size; it is that manual
cleanup reduced some train authors to low counts:

- `john_keats`: `25`
- `rudyard_kipling`: `22`
- `wilfred_owen`: `31`
- `robert_frost`: `37`
- `william_blake`: `45`

Those low-count train authors should be checked before using v4.4 as-is.
