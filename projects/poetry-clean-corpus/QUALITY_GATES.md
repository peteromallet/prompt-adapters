# Quality Gates

These gates apply before a corpus version can feed a pair dataset.

## Corpus-Level Gates

For `poetry_corpus_v0`:

- At least 25 retained authors.
- At least 10 unique clean records per retained author.
- At least 500 unique clean records total.
- Zero exact duplicate `clean_sha256`.
- Zero records with unknown license/public-domain basis.
- Artifact regex hit rate below 1%.
- Prose-like rejection candidates manually audited.

For a serious `poetry_corpus_v1`:

- 75+ retained authors.
- 25+ unique clean records for most train authors.
- 2,500+ unique clean records total.
- Heldout author set has at least 8 authors with 20+ records each.

## Row-Level Rejects

Delete rows with:

- Project Gutenberg license/footer/header residue.
- table of contents, index, advertisement, bibliography, preface, editorial
  prose, footnotes, source notes, or publication front matter.
- HTML tags, URLs, classroom prompts, form instructions, assessment language.
- OCR corruption that changes readability.
- prose paragraph structure unless the poem is intentionally prose poetry and
  the author/source justifies it.
- author/title mismatch.
- unclear copyright.

## Row-Level Edits

Small edits are allowed only for:

- removing a title line duplicated into the text,
- removing footnote markers,
- normalizing whitespace,
- trimming source boilerplate outside the poem.

Do not rewrite poem content.

## Pair-Dataset Gates

Before deriving `pairs_v5_0`:

- No train/val/test target duplicates by normalized text.
- Max rows per reference is capped.
- Max rows per target is capped.
- Heldout probes are balanced by author.
- Probe references and expected targets are clean corpus records.
- Pair manifest records all corpus snapshot hashes.

## Manual Audit Policy

Manual or subagent review should be focused:

- audit every source with high deterministic artifact rate,
- audit every retained author with fewer than 15 records,
- audit all heldout/probe records,
- audit random stratified samples from high-volume authors.

The review decision vocabulary is:

- `keep`
- `delete`
- `edit`
- `uncertain_delete`

Uncertain copyright or authorship defaults to delete.
