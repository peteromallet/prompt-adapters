# Author Provenance And Review

Status: active gate.

Short answer: every standardized corpus row can have an `author_id`, but that
does not mean every author assignment is scientifically acceptable.

## Current Behavior

For source-native corpus candidates:

- Project Gutenberg rows use the curated manifest author ID.
- Internet Archive rows derive `author_id` from the IA creator string when no
  normalized author is provided.

This guarantees a non-empty `author_id`, but IA creator strings can refer to:

- the actual poet,
- an editor,
- a compiler,
- a translator,
- a publisher,
- an anthology curator,
- a collective/magazine,
- a malformed metadata string.

Therefore IA-derived author IDs are candidates until reviewed.

## Current Candidate State

`poetry_corpus_v0_source_native_strict_candidate`:

- 61,598 standardized rows.
- 153 author IDs.
- 147 author IDs have at least 25 records.
- 176 fetched sources.
- 4 failed sources.
- zero duplicate clean text hashes.
- artifact-rate audit: 0.9237%, under the current 1% threshold.

But the author/source review queue says:

- 24 author IDs are `keep_candidate`.
- 129 author IDs need review.
- Common reasons: IA/non-Gutenberg source, risky author string, risky source
  title, single-source high volume, low record count.

Review queue:

`source_native_strict_author_review_queue.jsonl`

Summary:

`source_native_strict_author_review_summary.json`

`poetry_corpus_v0_source_native_accepted_candidate`:

- 51,634 rows.
- 127 author IDs.
- 147 accepted sources.
- deterministic artifact-rate audit: 0.67%.
- audit passes, but author identity and source type were still too loose.

`poetry_corpus_v0_source_native_curated_candidate_v9`:

- 24,614 rows.
- 79 normalized author IDs.
- 97 retained sources.
- all retained authors have at least 25 records.
- zero duplicate clean text hashes.
- deterministic artifact-rate audit: 0.0%.
- current best high-precision training candidate.

Curated candidates use:

`author_source_curation_v0.json`

The major review issue shifted from author coverage to source admission. v3-v9
removed or quarantined sources that repeatedly leaked line notes, front matter,
OCR artifacts, dramatic/prose material, or bad author assignment.

## Policy

Do not train on all 61,598 strict rows or all 51,634 accepted rows.

Curated v9 is good enough for the next pair-derived training experiment, but it
should still be treated as a candidate rather than a final archival corpus.
Further scale should come through the same source-review gate, not through raw
scraping or pair-level patching.

For `poetry_corpus_v0`, author/source acceptance must happen before pair
derivation:

- keep curated Gutenberg authors unless source-level samples reveal bad poem
  boundaries,
- review IA author strings before acceptance,
- reject anthologies assigned to editors/compilers,
- reject prose/criticism sources that merely contain poetry,
- reject translated classical material unless we explicitly want translator
  style,
- merge duplicate author IDs where the same author appears under multiple
  source-name variants,
- cap rows per source/author during pair derivation even for accepted authors.

## Practical Next Step

For broader v10+, use cheap review over author/source groups before row-level
review:

For each author/source group, decide:

- `accept_author_source`
- `reject_source`
- `merge_author_id`
- `needs_row_spotcheck`

This gives much higher leverage than row-level review because the main remaining
risk is source/author attribution, not isolated bad lines.
