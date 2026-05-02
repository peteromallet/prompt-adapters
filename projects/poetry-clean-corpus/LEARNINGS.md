# Learnings

## 2026-04-26

Experiment 025 changed the data strategy. Manual row cleanup and structural
balancing were useful, but they exposed the limitation of pair-first data:
after true dedupe, some authors had too few unique clean targets, and repeated
references had been helping the pathway.

Current belief:

- Build clean source-level poem corpora first.
- Treat pair datasets as deterministic derived artifacts.
- Optimize for unique clean poems/authors and provenance, not pair count.
- Do not scale with uncertain source quality; dirty scale teaches instruction
  following, prose drift, and source artifacts.

Immediate next artifact should be `poetry_corpus_v0`, not another GPU run.

Seed baseline created from v4.5 pair rows:

- `text-ip-adapter/data/poetry_corpus_v0_seed_from_v45`
- 1,059 unique cleaned records.
- 27 authors.
- no exact duplicate clean text hashes.
- every author has at least 10 records.
- deterministic artifact audit flagged 3 rows.

The seed passes broad numeric gates, but it is not sufficient as the final
corpus because provenance is inherited from pair rows, titles are mostly
missing, and source URLs are pseudo-provenance. It is useful as a baseline and
for audit tooling.

Audit calibration from the seed:

- `thomas_hardy_460cdd268db2` was a false positive: `teacher` appears in a real
  poem line, not a classroom prompt.
- `william_wordsworth_c7732da7d50d` was a false positive: `contents` appears as
  a normal verb phrase.
- `gerard_manley_hopkins_8a0ad81e7170` is a real source-apparatus concern:
  title/numbering, variant labels, and bracketed variant text remain. Future
  corpus cleaning needs a specific rule for textual variants/apparatus, not
  just generic artifact regexes.

Large-source survey:

- Internet Archive is a real scale lane. A broad English poetry-ish metadata
  query returned 136,885 hits; a conservative public-domain-ish query returned
  2,093 hits.
- The unfiltered conservative IA sample still includes modern uploads and
  ambiguous material. Filtering to known publication year <= 1929 and excluding
  handwritten-language records produced a cleaner 500-row candidate sample with
  390 unique creator strings, 16 missing authors, and 76 anthology-like records.
- IA should enter through metadata/source manifests first. Do not download OCR
  text or train from it until author normalization, rights/date checks,
  anthology/editor handling, and OCR quality gates are implemented.

First source-native build:

- `poetry_corpus_v0_source_native_candidate`: 83,375 rows from 209 fetched
  sources, but too much IA source/author noise.
- `poetry_corpus_v0_source_native_strict_candidate`: 61,598 rows from 176
  fetched sources, 153 author IDs, zero duplicate clean text hashes, artifact
  rate 0.9237%.

The strict candidate has enough scale, but it is not yet accepted. The
remaining blocker is author/source provenance. IA creator strings can represent
editors, compilers, translators, publishers, anthologies, or malformed metadata.
The author review queue currently marks 129/153 author IDs for review and only
24 as keep-candidates. This is the correct next gate: review author/source
groups before doing any pair derivation.

Source acceptance and deterministic curation changed the working corpus:

- `poetry_corpus_v0_source_native_accepted_candidate`: 51,634 rows, 127
  authors, 147 accepted sources, deterministic artifact rate 0.67%, audit
  passes. This was useful but still mixed duplicate author identities and
  translation/editor sources.
- `poetry_corpus_v0_source_native_curated_candidate_v2`: 32,609 rows, 90
  normalized authors, 110 retained sources, zero duplicate clean hashes, audit
  artifact rate 0.0%, all authors >=25 records.

Concrete curation fixes applied:

- Merged duplicate IDs for Shelley, Tennyson, Shakespeare, Amy Lowell,
  Rossetti, Chesterton, Masefield, Wordsworth, Yeats, Elizabeth Barrett
  Browning, and Rupert Brooke.
- Rejected editor/translator/anthology/classical-translation buckets such as
  Edward Arber, Karl Knortz, Leo Wiener, Sylvanus Morley, Virgil, Horace,
  Schiller, Omar Khayyam, and criticism/prose sources.
- Rejected obvious source contaminants: Shakespeare plays-and-poems volumes,
  Yeats IA drama/prose leakage, Amy Lowell criticism/translation sources,
  Jacobite song anthology, Montagu letters, Pearse collected plays/stories,
  Wheatley memoir, and Poe biography-heavy source.
- Added row-level filters for deterministic audit flags, dramatic speaker
  headings, stage directions, French prose leakage, line-note/front-matter
  snippets, and explicit editorial prose.

The parser/source precision pass continued through curated v9. Instead of
trying to salvage every collected edition, the curation layer quarantined whole
sources that repeatedly leaked apparatus, front matter, OCR junk, misassigned
authors, or non-poetry material.

Current high-precision corpus:

- `poetry_corpus_v0_source_native_curated_candidate_v9`: 24,614 rows, 79
  normalized authors, 97 retained sources.
- all authors have at least 25 records.
- zero duplicate clean text hashes.
- deterministic artifact audit passes with artifact_rate=0.0.

The first conservative pair dataset has also been derived:

- `pairs_v5_0_poetry_corpus_curated`: train 4,886 rows / 65 authors, val 168
  rows / 7 authors, test 168 rows / 7 authors.
- author-disjoint splits.
- max_ref_repeat=1 and max_target_repeat=1 in every split.
- probe set has 14 rows because val+test contain 14 total authors.

This changes the next action. The blocker is no longer “repair before any GPU
run”; the next best scientific move is a small v5.0 training run to test whether
high-precision source-native poetry data improves generations without reviving
collapse. If it works, broaden the corpus with the same gates. If it fails,
diagnose objective/checkpoint/length settings before adding more data.
