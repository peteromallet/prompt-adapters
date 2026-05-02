# Corpus Spec

This project builds a clean corpus first. Pair datasets are derived views over
this corpus.

## Canonical Row Schema

Each JSONL row represents one poem or coherent poem chunk.

Required fields:

- `corpus_id`: stable ID for this cleaned record.
- `author_id`: normalized snake-case author identifier.
- `author_name`: display name.
- `title`: poem/chunk title if known; otherwise `null`.
- `text`: cleaned poem text.
- `source_id`: stable source manifest ID.
- `source_name`: source family, e.g. `project_gutenberg`, `wikisource`.
- `source_url`: URL or local source reference.
- `source_work_title`: book/collection/page title if known.
- `source_publication_year`: integer or `null`.
- `license`: e.g. `public_domain_us`.
- `public_domain_basis`: short reason, e.g. `published_before_1930_us`.
- `raw_sha256`: hash of raw source text.
- `clean_sha256`: hash of cleaned `text`.
- `cleaning_version`: code/spec version used to produce this row.
- `split_hint`: optional `train`, `val`, `test`, `probe`, or `null`.
- `flags`: list of audit flags, empty if clean.

Recommended fields:

- `source_line_start`
- `source_line_end`
- `chunk_index`
- `is_complete_poem`
- `meter_or_form`
- `language`
- `notes`

## Hard Invariants

- `text` is the poem/chunk only: no table of contents, editor note, front
  matter, classroom instruction, HTML, URLs, footnotes, or OCR headers.
- `author_id` is the actual author of the poem, not editor, translator, page
  compiler, or anthology title.
- `clean_sha256` is unique within a corpus version.
- A retained author must have enough unique records for both reference and
  target sampling. The v0 minimum is 10; the intended training minimum is 25+.
- Copyright status must be explicit. Unknown means reject.

## Pair Derivation Rules

Pair datasets must not invent data quality. They may only select from clean
corpus rows.

Default pairing rules:

- Reference and target must be different `corpus_id`.
- Cap targets per reference.
- Cap references per target.
- Cap rows per author.
- Keep heldout authors out of train.
- Keep probe rows deterministic and balanced.
- Preserve all source provenance in derived pair rows.

## Version Naming

- `poetry_corpus_v0`: first gated clean-corpus candidate.
- `pairs_v5_0`: first pair dataset derived from `poetry_corpus_v0`.

Breaking changes to cleaning logic or source eligibility should create a new
corpus version, not mutate an existing one.
