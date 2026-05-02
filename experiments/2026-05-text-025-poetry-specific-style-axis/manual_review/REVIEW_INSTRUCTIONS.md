# v4.3 Poetry Manual Review Instructions

Goal: preserve clean author-style poetry pairs and remove rows that teach the
adapter bad behavior. Write decisions only to your assigned review JSONL file.
Do not edit the source dataset and do not edit other review files.

## Input

Each shard row includes:

- `split`
- `row_index`
- `author`
- `ref_text`
- `target_text`

Probe rows use:

- `reference_text`
- `expected_target`
- `swap_reference_text`

## Output Schema

Write exactly one JSON object per input row:

```json
{
  "split": "train",
  "row_index": 123,
  "author": "emily_dickinson",
  "decision": "keep",
  "reason": "clean",
  "confidence": "high",
  "ref_text_clean": null,
  "target_text_clean": null,
  "notes": "short note"
}
```

Allowed `decision`: `keep`, `delete`, `edit`.

Allowed `confidence`: `high`, `medium`, `low`.

For `keep` and `delete`, clean fields must be `null`. For `edit`, include the
full replacement text for the fields you changed and `null` for untouched
fields. For probe rows, use `reference_text_clean`, `expected_target_clean`, and
`swap_reference_text_clean` if needed.

## Reasons

Use one primary reason:

- `clean`
- `meta_instruction`
- `prose_drift`
- `source_artifact`
- `wrong_register`
- `bad_chunk`
- `duplicate`
- `style_outlier_bad_data`
- `heading_or_wrapper`
- `too_short`
- `uncertain_keep`

## Delete Rows When

- They contain meta-writing or instruction leakage:
  - "write a poem"
  - "try to write"
  - "use the following lines"
  - "the reader"
  - "the poet's perspective"
  - "this poem is about"
  - "first attempt"
  - classroom/summary/explanation language
- They are prose drift:
  - essay paragraphs
  - literary criticism
  - biographies
  - prefaces/intros
  - "In his work..."
  - "The author considers..."
  - long paragraph blocks with no verse lineation
- They are wrong register:
  - screenplay dialogue
  - speaker labels like `BURR`, `HAMILTON`, `SCENE`, `ACT`, `ENTER`, `EXIT`
  - dramatic script material unless clearly a poem and style-useful
- They contain source artifacts that cannot be cleanly removed:
  - Gutenberg/license material
  - footnote blocks
  - page/image captions
  - URLs
  - bracketed citation clusters
  - table-of-contents fragments
- They are bad chunks:
  - only a title or heading
  - orphan fragment too short to learn from
  - starts/ends in a way that destroys coherence
  - unrelated poems glued together
- They are same-author style outliers best explained by contamination:
  - wrong subgenre/source under the author
  - prose/editorial voice
  - modern instruction-like generic verse
  - wildly inconsistent row compared to nearby same-author rows for non-literary reasons

## Edit Rows When

- A title/header/wrapper can be removed and the remaining poem is good.
- A footnote marker or source line can be stripped.
- A bad first/last line contaminates otherwise good verse.
- A row contains a clean poem plus removable editorial wrapper.

## Keep Rows When

- It is clearly verse.
- It reflects the assigned author or plausible author variation.
- It has coherent line breaks.
- It does not instruct the model how to write.
- It does not summarize or explain poetry.
- It is style-bearing, not just generic meta text.

## Style-Inconsistent Rows

Yes, look for rows that feel inconsistent with the same author. Delete only when
the mismatch is likely bad data, wrong register, broken chunking, source
contamination, or editorial/prose material. Do not delete legitimate author
range: early/late style changes, dramatic monologue, narrative poems, comic
poems, religious poems, archaic diction, or line-length variation.

If uncertain but plausible, choose `keep` with reason `uncertain_keep` and
confidence `medium` or `low`.

## Probe Rows

Be stricter for probes than training rows. Probe refs, expected targets, and
swap refs should be pristine poetry. Delete or edit any probe row with meta
language, prose, dramatic script contamination, or a bad swap reference.
