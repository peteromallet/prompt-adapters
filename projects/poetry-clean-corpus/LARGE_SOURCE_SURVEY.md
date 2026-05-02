# Large Source Survey

Status: initial survey, 2026-04-26.

The answer is yes: there are much larger poetry sources than the hand-curated
Gutenberg list. The constraint is not availability; it is legal/source quality
and poem-boundary reliability.

## Best Large Lanes

### 1. Allison Parrish Gutenberg Poetry Corpus

Source:

- GitHub: https://github.com/aparrish/gutenberg-poetry-corpus
- Kaggle mirror: https://www.kaggle.com/datasets/thehung83/gutenberg-poetry-corpus

Reported scale:

- About 3,085,117 lines of poetry.
- About 1,191 unique Project Gutenberg IDs.
- Public-domain-oriented Gutenberg source selection.

Pros:

- Much broader than our current 36 Gutenberg source candidates.
- Already mined specifically for poetry lines.
- Good way to discover source IDs and poetry-heavy books.

Risks:

- Line-level corpus, not poem-level corpus.
- Author/title/poem boundaries may need reconstruction from Gutenberg metadata
  and source texts.
- We must not train directly on shuffled lines; use it for discovery and
  source prioritization first.

### 2. Internet Archive Public-Domain Poetry Candidates

Discovery query used:

`mediatype:texts AND (title:poems OR title:poetry OR subject:poetry) AND (language:English OR language:eng) AND (rights:publicdomain OR licenseurl:*publicdomain*)`

Observed via Advanced Search API:

- Conservative public-domain-ish poetry query: 2,093 hits.
- Broader English poetry-ish texts query: 136,885 hits.

Artifacts:

- `text-ip-adapter/data/poetry_source_manifest_ia_publicdomain_candidates.jsonl`
- `prompt-adapters/projects/poetry-clean-corpus/source_manifest_ia_publicdomain_candidates.jsonl`
- `text-ip-adapter/data/poetry_source_manifest_ia_pre1930_candidates.jsonl`
- `prompt-adapters/projects/poetry-clean-corpus/source_manifest_ia_pre1930_candidates.jsonl`

Current sample:

- First 500 conservative candidates persisted.
- First 500 pre-1930 conservative candidates persisted.
- Pre-1930 profile: 390 unique creator strings, 16 missing authors, 76
  anthology-like records.

Pros:

- Scale is large enough to solve author/source coverage if filtered well.
- Metadata includes title, creator, date, subject, license/right hints.

Risks:

- OCR quality varies heavily.
- Metadata can be wrong or vague.
- Some records are manuscripts, anthologies, criticism, or single-poem scans.
- Rights metadata is only a candidate signal; it still needs verification.

### 3. Wikisource

Source:

- https://en.wikisource.org/wiki/Poems

Pros:

- Public-domain/free-license orientation.
- Better page structure than raw OCR for many works.
- Often has author/work/page hierarchy.

Risks:

- Category/page crawling required.
- Some pages are disambiguation/index pages.
- Must preserve license and page provenance.

### 4. Standard Ebooks

Sources:

- https://standardebooks.org
- https://github.com/standardebooks

Observed:

- Standard Ebooks has 1,300+ public repositories.
- It is high quality and public-domain-oriented, but poetry is a smaller subset.

Pros:

- Very high text quality.
- Structured XHTML/EPUB source.
- Good for canonical major authors.

Risks:

- Not enough volume alone.
- GitHub discovery needs repository metadata filtering.

### 5. HathiTrust / HTRC

Sources:

- HathiTrust and HathiTrust Research Center metadata/extracted features.
- Recent datasets around American poetry in HathiTrust.

Pros:

- Potentially huge.
- Strong library metadata.

Risks:

- Access and full-text rights are more complex.
- May be better as a metadata discovery layer than immediate text source.

## Sources to Avoid as Primary Text

- Poetry Foundation full archive: valuable for reference, but terms/content
  ownership make bulk reuse risky unless we restrict to explicitly public-domain
  subset and verify permissions.
- Modern poetry archives with contemporary authors.
- Classroom, lesson-plan, and quote sites.
- Random “public domain poems” websites without provenance.

## Updated Strategy

Do not manually enumerate authors first. Build a source-discovery layer:

1. Use Allison Parrish / Gutenberg Poetry Corpus to discover poetry-rich
   Gutenberg IDs.
2. Use Internet Archive API to discover candidate public-domain poetry volumes.
3. Use Wikisource and Standard Ebooks as high-quality structured source lanes.
4. Normalize all candidates into source manifests.
5. Accept sources only after source-native text extraction, OCR/artifact audit,
   license check, and poem-boundary confidence.

For Internet Archive specifically, use pre-1930/date-filtered manifests as the
first pass. The broad query contains modern uploads and ambiguous public-domain
marks; the pre-1930 filter produces a better candidate pool, though it still
contains anthologies, editors, lectures about poetry, magazines, and OCR risk.

The broad-data path should therefore be:

`source discovery -> source manifest -> source-native corpus rows -> corpus audit -> frozen corpus -> pair derivation`

not:

`scrape lots of text -> make lots of pairs -> hope cleanup catches it`.
