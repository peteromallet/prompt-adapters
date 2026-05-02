# Data Spotcheck: v9 Corpus / v5.0 Pairs

Status: good enough for the current experiment, not good enough to freeze as a
final corpus.

## What Looks Good

- Pair structure is finally sane: author-disjoint splits, unique references,
  unique targets, and no repeated-reference/target crutch.
- Many sampled Gutenberg and clean IA rows are real verse, not instruction
  templates or boilerplate.
- The v5.0 training preflight saw all expected files and loaded 4,886 train
  rows.
- The 006 warm-start checkpoint exists on the RunPod network volume.

## Main Problems Found

The remaining contamination is no longer the old v2 failure mode of repeated
targets and instruction-like templates. It is mostly source quality:

- IA OCR degradation: garbled letters, stray carets, broken words, page numbers,
  and old scans with low character fidelity.
- Front matter / table-of-contents leakage in some IA sources.
- Some prose/editorial chunks still pass as poem rows.
- A few archaic-spelling sources are technically poetry but may be too noisy for
  style learning unless explicitly desired.

## High-Risk Buckets From Pair Audit

Quarantine or manually review these before a v10 corpus:

- `wright_thomas_1810_1877` / `internet_archive_songsandcarolswright`: val rows
  include prose and very OCR-heavy Middle English-like text.
- `huntingtower_catherine_rebecca_grey_talmash_baroness_1766_or_7_1852` /
  `internet_archive_bub_gb_O0-76ON5C1MC`: many OCR-symbol hits.
- `letitia_elizabeth_landon` / `internet_archive_bub_gb_JncEAAAAQAAJ`: many OCR
  distortions.
- `eaton_arthur_wentworth_hamilton_1849_1937` /
  `internet_archive_PoemsOfTheChristianYear`: table-of-contents leakage.
- `leo_xiii_pope_1810_1903` /
  `internet_archive_PoemsCharadesInscriptionsOfPopeLeoXIII`: prose notes and
  translation/context paragraphs.
- `thomas_campbell` / `internet_archive_bub_gb_JCd6p41jH-oC`: prose historical
  intro leakage.

## Current Experiment Interpretation

Let experiment 026 finish. It is still a useful scientific test because the pair
dataset fixes the largest known structural issues and has enough clean poetry to
test the direction.

If experiment 026 qualitatively improves over v4.5, the next corpus pass should
be v10 with stricter OCR/source gates. If it fails, do not assume “clean corpus”
is wrong; separate objective/checkpoint issues from the source-quality layer.
