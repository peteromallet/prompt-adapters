# Poetry cleanup audit

Scope: `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/{train,val,test}.jsonl` plus `text-ip-adapter/scripts/build_v3_pairs.py`.
Method: scanned only rows with `register == "poetry"`, counted exact target-text markers, and cross-checked the existing build filters in `build_v3_pairs.py`.

## What survived

| Artifact class | train | val | test | Notes |
| --- | ---: | ---: | ---: | --- |
| Note/page labels | 2 rows / 1 doc | 0 | 0 | `william_wordsworth_b284eb2de7b4` has `NOTE I.` and `PAGE I (9).--...` |
| Prose/editorial apparatus | 5 rows / 3 docs | 0 | 0 | `edgar_allan_poe_18e9725f7eb1`, `edgar_allan_poe_4a0aa6970a62`, `wilfred_owen_34a59fd395b4` |
| Picture captions | 0 | 33 rows / 15 docs | 0 | All are `"[Picture: ...]"` lines in Hardy poems |
| Play/performance cues / section labels | 1 row / 1 doc | 1 row / 1 doc | 8 rows / 3 docs | Train case is the standalone `CONTINUED.` leak in `matthew_arnold_3cbb347bf510` |
| Exact prompt leakage | 0 | 0 | 0 | No poetry row matched `write a \\d+ word essay`, `reference passage`, or `same broad subject` |

## Exact fix candidates

Safe regex/rule additions:

```python
# drop obvious apparatus
r"(?m)^\s*(?:NOTE ON .+|NOTES\.?|NOTE\s+[IVXLCDM0-9]+\.?|PAGE\s+[IVXLCDM0-9]+(?:\s*\(\d+\))?\.\-\-)\s*$"

# drop illustration captions
r"(?m)^\s*\[Picture:[^\]]+\]\s*$"

# drop explicit performance cues
r"(?mi)^\s*\(_As sung by_[^)]+\)\s*$|^\s*\((?:Full\s+)?Chorus\)\b|^\s*\((?:Bugle|Cornet):[^)]*\)\s*$"
```

Do not broaden `Chorus` or `Act` into a generic word filter. That would hit ordinary poems and dramatic verse too often.

## High-confidence blocklist if regex feels unsafe

Use `target_doc_id` blocklist for the play-form/performance cases that are easiest to overmatch:

```json
[
  "matthew_arnold_3cbb347bf510",
  "sara_teasdale_3033dc38f597",
  "thomas_hardy_f35ac0ff4c05",
  "rudyard_kipling_0ae181241f9d",
  "rudyard_kipling_0bb24c3b271b",
  "rudyard_kipling_decbe36af8db"
]
```

## Build-script gap

`build_v3_pairs.py` already filters `LINENOTES`, `PAGE <n>`, `First published in <year>`, `EDITED BY`, `AUTHOR OF`, `BOOK <roman>`, `was born in`, `attended a school`, `Voice of the Page`, and repeated 5-grams.

It does not currently cover:

* `NOTE ON ...` / `NOTES.`
* `PAGE I (9).--...` style page labels
* `[Picture: ...]` captions
* standalone `CONTINUED.` lines
* explicit stage/performance cue lines

## Bottom line

The surviving poetry contamination is mostly apparatus, not prompt leakage. The cleanest deterministic win is to add exact note/page/picture-caption filters and then block the few play-form target docs above instead of trying to regex all stage-like poetry.
