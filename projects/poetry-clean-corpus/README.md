# Poetry Clean Corpus Project

Status: active corpus-build project.

Purpose: build a source-level clean poetry corpus that future pair datasets are
derived from. This is deliberately separate from training experiments. The
training track should consume versioned corpus snapshots, not scrape and clean
inside experiment scripts.

## Why This Exists

Experiment 025 showed that cleaning was necessary and useful, but also that
pair-level cleanup is the wrong permanent abstraction:

- v4.4 manual cleanup removed many bad rows, but structural duplicate artifacts
  remained.
- v4.5 structural balancing fixed repeated references, duplicate targets, and
  probe imbalance.
- The pathway survived (`cos_K_last_swap=0.4340`), but author coverage was thin
  after true dedupe, and surface failures remained.

The conclusion is that we need more unique clean poetry and stronger provenance,
not more pair expansion from a small noisy pool.

## Project Goal

Produce a versioned public-domain poetry corpus where each row is a clean poem
or coherent poem chunk with enough metadata to audit, reproduce, and pair
conservatively.

The corpus should support:

- broader author/style coverage,
- many unique reference contexts per author,
- heldout splits by author and by poem,
- deterministic pair generation with caps,
- reliable probe construction,
- source-level audits before any GPU run.

## Non-Goals

- Do not train directly from scraped raw text.
- Do not create a large pair dataset before the clean corpus passes gates.
- Do not use row count as the main quality metric.
- Do not admit uncertain copyright/licensing material.

## Immediate Milestone

Build `poetry_corpus_v0` from known public-domain sources with strict metadata
and audits. Current best candidate is:

- `text-ip-adapter/data/poetry_corpus_v0_source_native_curated_candidate_v9`
- 24,614 rows.
- 79 normalized author IDs.
- 97 retained sources.
- all retained authors have at least 25 records.
- zero duplicate clean text hashes.
- deterministic artifact audit passes with artifact rate 0.0%.

This is not a final forever corpus, but it is the first high-precision candidate
worth training against. v3-v9 deliberately sacrificed scale by quarantining
contaminated collected editions, bad IA OCR/front-matter sources, and
misassigned sources rather than letting apparatus leakage enter the pair set.

Original v0 target:

- 25-50 authors,
- at least 10 clean poem/chunk records per retained author,
- no exact duplicate poem texts,
- no obvious source artifacts,
- manual spotcheck of high-risk authors/sources,
- deterministic split manifest.

The first derived pair dataset now exists:

- `text-ip-adapter/data/pairs_v5_0_poetry_corpus_curated`
- train: 4,886 rows, 65 authors.
- val: 168 rows, 7 authors.
- test: 168 rows, 7 authors.
- author-disjoint splits.
- max reference and target repeat count is 1 in every split.
- probes file has 14 rows, one for each val/test author.

Next action is the small v5.0 training run, then qualitative and metric
evaluation before any broad data scale-up.

## Files

- `CORPUS_SPEC.md` — row schema and invariants.
- `SOURCE_PLAN.md` — source acquisition plan and source risk.
- `LARGE_SOURCE_SURVEY.md` — broader source lanes beyond the current
  hand-curated Gutenberg list.
- `QUALITY_GATES.md` — acceptance checks before pair generation.
- `LEARNINGS.md` — running project-level findings.
- `source_manifest_v0_candidates.jsonl` — initial Gutenberg candidate source
  manifest; candidates are not accepted until source-native audits pass.
- `source_manifest_ia_publicdomain_candidates.jsonl` — first 500 conservative
  Internet Archive public-domain-ish poetry candidates.
- `source_manifest_ia_pre1930_candidates.jsonl` — first 500 conservative
  Internet Archive candidates with known publication year <= 1929 and no
  handwritten-language marker.
- `AUTHOR_PROVENANCE_AND_REVIEW.md` — author assignment policy and current
  review queue interpretation.
- `author_source_curation_v0.json` — deterministic author/source/row curation
  rules used to build the curated candidates.
- `source_native_curated_candidate_v9_audit_summary.json` — audit result for
  the current best candidate.
