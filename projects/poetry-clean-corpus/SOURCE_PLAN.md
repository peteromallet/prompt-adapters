# Source Plan

The source expansion target is unique clean poems/chunks, not pair count.

## Source Priority

### Tier 1: Low Risk

Use first.

- Project Gutenberg author collections with clear public-domain status.
- Allison Parrish's Gutenberg Poetry Corpus as a discovery layer for
  poetry-heavy Gutenberg IDs.
- Wikisource author/work pages that are public-domain and have clean page
  structure.
- Standard Ebooks poetry editions where source XHTML/EPUB structure is clean.
- Public-domain collected works from reliable scans where poem boundaries are
  visible.

### Tier 2: Medium Risk

Use after Tier 1 tooling works.

- Internet Archive scans with OCR, but only with strong artifact filters and
  manual spotchecks.
- HathiTrust/HTRC metadata or extracted-feature workflows, subject to access
  and rights constraints.
- Public-domain anthologies, if author/title attribution is reliable.

### Tier 3: Avoid Unless Necessary

- Modern poetry websites with unclear reuse terms.
- Copyright-ambiguous twentieth-century material.
- Classroom/lesson-plan pages.
- Quote databases.
- Pages where poem text is mixed with commentary and not structurally separable.

## Acquisition Strategy

1. Build a source manifest before fetching text.
2. Fetch raw source text into immutable cache paths.
3. Normalize and segment to poem/chunk records.
4. Run deterministic audits.
5. Manually spotcheck sources/authors with high deletion or artifact rates.
6. Freeze a corpus version only after gates pass.

## Initial Author Target

The first broad clean target should favor older public-domain authors with
substantial available work. Example seed categories:

- Romantic and Victorian: Wordsworth, Blake, Keats, Shelley, Coleridge,
  Tennyson, Elizabeth Barrett Browning, Robert Browning, Christina Rossetti.
- American nineteenth/early twentieth: Dickinson, Whitman, Poe, Longfellow,
  Robinson, Teasdale, Millay where public-domain basis is clear.
- Modernist public-domain subset: Eliot/Pound only where specific works are
  public-domain and cleanly sourced.

Thin authors should not be forced into train if they cannot meet corpus gates.

## Source Manifest Fields

Each source candidate should be represented before ingestion:

- `source_id`
- `author_id`
- `author_name`
- `source_name`
- `source_url`
- `source_work_title`
- `source_publication_year`
- `license`
- `public_domain_basis`
- `expected_register`
- `risk_notes`
- `status`: `candidate`, `fetched`, `ingested`, `rejected`, `accepted`
