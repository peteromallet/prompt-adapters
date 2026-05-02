# Speech cleanup audit

Scope: only `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/{train,val,test}.jsonl` plus `text-ip-adapter/scripts/build_v3_pairs.py`.

## What I checked

- Parsed the three split files with `json.JSONDecoder().raw_decode(...)` because the file contents are concatenated JSON objects with embedded newlines, so plain line-by-line JSONL parsing is unreliable.
- Reviewed the builder logic around:
  - `_clean_boilerplate_text` at `scripts/build_v3_pairs.py:157-164`
  - `_suspicious_reasons` at `scripts/build_v3_pairs.py:194-220`
  - `_load_blocklist` / `_apply_blocklist` at `scripts/build_v3_pairs.py:244-280`
  - split/audit wiring at `scripts/build_v3_pairs.py:531-576`
- Searched `target_text` and `ref_text` for transcript boilerplate, public-record headers, generic assignment/no-ref phrases, and short/over-generic targets.

## Findings

### 1. Transcript boilerplate

No live `target_text` hits in any split for literal transcript boilerplate:

- `^(view\s+)?transcript[\s:.-]*`
- whole-line `transcript`
- whole-line `view transcript`
- whole-line `download transcript`

Counts: train `0`, val `0`, test `0`.

This matches the current builder cleanup: transcript labels are already stripped, and I did not find remaining target-side transcript residue.

### 2. Remaining speech/public-record residue

The only high-confidence residue I found is the formulaic public-record header family in speech targets. This is much narrower than the broad `SUSPICIOUS_TARGET_PATTERNS` in the builder, which would overmatch normal speeches if used wholesale.

Counted by `target_text` hits:

| Split | Pair hits | Unique target docs |
| --- | ---: | ---: |
| train | 28 | 15 |
| val | 5 | 1 |
| test | 2 | 1 |

High-confidence target docs for hard blocklisting if regex is considered too risky:

- train: `arthur_2ac1ad2248d7`, `arthur_9abdb3596ba4`, `cleveland_0e3895af0ee3`, `cleveland_705671961b36`, `cleveland_89c226f1ea97`, `cleveland_939f44d9e741`, `cleveland_d5976c7ae5e5`, `cleveland_fdce34a696f1`, `coolidge_4e86f8fc3889`, `coolidge_e8d2ef8c46aa`, `fdroosevelt_56fded7fa8da`, `mckinley_54ec54ff8a3a`, `mckinley_fe41b4cd910c`, `pierce_d783b6dad898`, `wilson_f178eae4c348`
- val: `vanburen_252695e763b5`
- test: `theodore_roosevelt_47709e35a2c7`

These are the only IDs I would block by hand before using a broader regex gate.

### 3. Generic assignment / no-ref contamination

No target-side hits in the current splits for:

- `write a \d+ word essay`
- `the reference passage`
- `use the reference passage for style`
- `write a piece in the style of the reference passage`

Counts: train `0`, val `0`, test `0`.

The builder still contains the generic instruction path at `GENERIC_STYLE_INSTRUCTION` / `instruction_mode="generic"`, but that is a prompt-generation choice, not live target-text contamination in these files.

### 4. Too-generic targets

I did not find short target texts in the speech split that would justify an extra cleanup rule:

- `len(target_text) < 100`: train `0`, val `0`, test `0`

### 5. Author confusion

I did not find a high-confidence author-mismatch pattern in the current speech rows. The obvious residue here is public-record boilerplate, not cross-author leakage.

## Proposed deterministic rules

Use the following in order:

1. Keep the existing transcript stripper:
   - `^(view\s+)?transcript[\s:.-]*`
   - whole-line `transcript|view transcript|download transcript`
2. Add a speech-only exact-header gate for public-record openings, but prefer the doc-id blocklist above if regex scope is uncertain:
   - `(?i)^(?:by the president of the united states of america|a proclamation|to the congress(?: of the united states)?)`
3. Do not apply the builder’s broader public-record regexes blindly to speech. They match many legitimate speeches with normal presidential/congressional openings.
4. No extra rule is justified for generic assignment/no-ref contamination in the current files.

## Bottom line

Current splits look clean for transcript boilerplate and generic assignment/no-ref contamination. The only remaining speech-specific cleanup candidate is the small public-record header family listed above, and if regex risk matters, hard-block those 17 `target_doc_id`s instead of trying to generalize further.
