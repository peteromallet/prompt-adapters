# Screenplay Cleanup Audit

Scope: only `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/{train,val,test}.jsonl` and `text-ip-adapter/scripts/build_v3_pairs.py`.

## What I Checked

I scanned the split files with a line-aware JSON parser and regexes targeted at screenplay residue:

- bare page numbers
- standalone `CONTINUED` boilerplate
- malformed / fragmentary screenplay chunks
- OCR / table-layout noise
- duplicate headings / repeated scene-header patterns

I also reviewed the current build logic in `build_v3_pairs.py`. The screenplay-specific filter only covers bare page numbers today (`SCREENPLAY_ARTIFACT_PATTERNS`), while `_clean_boilerplate_text()` only strips transcript boilerplate.

## Current Coverage In Build

- `build_v3_pairs.py:84-88` has only `^\s*\d{1,4}\.\s*$` for screenplay artifacts.
- `build_v3_pairs.py:194-217` applies that check, but only after inspecting `target_text` and `ref_text`.
- `build_v3_pairs.py:157-163` only removes transcript/view-transcript/download-transcript prefixes.

## Residual Screenplay Artifacts Found

Counts below are affected rows / pairs, not unique `target_doc_id`s. I treated the last three buckets as conservative upper bounds because the heuristics can also catch normal screenplay formatting.

| Artifact class | train | val | test | Notes |
|---|---:|---:|---:|---|
| Bare page-number line (`^\s*\d{1,4}\.?\s*$`) | 1362 | 22 | 0 | Safe to strip deterministically |
| Standalone `CONTINUED` boilerplate (`(CONTINUED)`, `CONTINUED:`, `CONT'D` on its own line) | 234 | 20 | 0 | Safe to strip deterministically |
| Malformed / fragmentary chunk | 102 | 2 | 0 | Conservative short/fragment heuristic |
| OCR / table-layout noise | 1644 | 4 | 11 | Upper bound from line-separator / pipe / numeric clutter heuristic |
| Duplicate-heading / repeated scene-header pattern | 2719 | 26 | 35 | Upper bound from repeated-header heuristic |

015 sampled outputs show the same family of failures: page-number bleed (`504.`, `278.`) and prompt leakage in screenplay variants. So the corpus residue is consistent with what was visible after decoding.

## Deterministic Cleanup Rules

Use these as row-safe text cleanup before any row-level blocking:

```regex
# remove bare page numbers
^\s*\d{1,4}\.?\s*$

# remove standalone continuation boilerplate
^\s*(?:\(?CONTINUED\)?(?:[:.]| TO NEXT PAGE)?|CONT'D\.?)\s*$
```

Do not generalize the page-number rule beyond standalone lines. It is safe for this corpus, but the OCR/layout and duplicate-heading cases are too structurally mixed for a broad regex sweep.

## High-Confidence `target_doc_id` Blocklist Seeds

If you decide regex cleanup is too risky for a given row set, block these first. These rows already combine page/continued noise with OCR/layout or repeated-heading contamination.

### train

`12_years_a_slave_45c01a2d884b`, `12_years_a_slave_909e209e45a9`, `12_years_a_slave_9656c01b28fc`, `12_years_a_slave_9bd340372cea`, `12_years_a_slave_c6172397b283`, `2012_748d42cd150c`, `a_scanner_darkly_28c5269d37f5`, `a_scanner_darkly_6fa5e5cca5c3`, `a_scanner_darkly_ab9946ad0f84`, `a_scanner_darkly_f4fa6cca58f5`, `127_hours_b5371a426a9b`, `17_again_08571c934f48`, `17_again_5cd11fa3476b`, `17_again_880f9b04f93e`, `28_days_later_16e98c68cd4b`, `28_days_later_242507f2d15e`, `30_minutes_or_less_392e76da146b`, `500_days_of_summer_4e73516e87ad`

### val

`12_and_holding_a6bd8e2335c4`, `12_and_holding_bd6f1970619b`, `12_and_holding_e6b133e366b6`, `12_and_holding_185beed4235b`, `12_and_holding_66a978dc37ed`, `12_and_holding_53179b83fe45`

## Commands / Logic Used

- `rg -n` against `build_v3_pairs.py` and the 015 experiment notes to locate existing filters and the decoded-sample failure mode.
- `sed -n` on `README.md` and the 015 `samples.jsonl` to confirm the screening artifacts that motivated this audit.
- A Python line scanner over the three split files using `json.loads(line)` per record, then regexes per line inside `target_text` / `ref_text` to count the artifact classes above.

