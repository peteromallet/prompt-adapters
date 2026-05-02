# Source expansion plan (v2 corpus)

Target: replace the current ~971-pair / 328-unique-ref corpus with a diverse multi-source corpus that lifts the ref-diversity ceiling from ~300 to ~3000+ unique references across 4 registers.

## Datasets in scope (Phase 1)

| Register | Primary | License | Size | Parse effort |
|---|---|---|---|---|
| Poetry | **linhd-postdata/pulpo** (HF) | CC0 | 17.6M rows, 14 langs | Easy (HF `load_dataset`) |
| Speech | **UN General Debate Corpus** (Harvard Dataverse DOI:10.7910/DVN/0TJX8Y) | Public domain | 10,568 speeches × 195 countries × 77 yrs | Medium (CSV + text files) |
| Screenplay/plays | **DraCor** (dracor.org) | CC-BY 4.0 | 4,000+ plays across 9 language corpora | Medium (TEI-XML parse, has Python API `pydracor`) |
| Essay | **BEE-spoke-data/medium-articles-en** (HF) | MIT | 180,358 articles | Easy (HF `load_dataset`) |

Phase 2 (optional, only if Phase 1 under-delivers): Congressional Dataset, MovieSum, LongForm, Gutenberg plays.

Skipped (requires credentials): Poetry Foundation (Kaggle), HathiTrust BIPOC (Data Capsule).

## Target schema (matches existing `.llm.jsonl`)

Each row in output `.jsonl`:

```json
{
  "register": "poetry|speech|screenplay|essay",
  "author": "<slug>",
  "source_dataset": "pulpo|un_debate|dracor|medium",
  "ref_doc_id": "<slug>_<hash8>",
  "target_doc_id": "<slug>_<hash8>",
  "ref_text": "...",
  "target_text": "...",
  "instruction": "<rule-based placeholder; gets rewritten by haiku cleanup>",
  "instruction_rule_based": "<preserve original>",
  "metadata": {"era": "...", "language": "...", "geography": "..."}
}
```

## Anti-bias enforcement (hard caps, applied after ingestion)

1. **Per-author**: ≤ 2% of total corpus (at ~50k pairs that's ~1000 per author max)
2. **Per source_document**: ≤ 0.5% of total corpus (prevents `washington_a4e664f5849d` 199× star)
3. **Per register**: rebalance to no more than 40% share per register (prevents screenplay domination)
4. **Per source_dataset**: ≤ 50% share (prevents PULPO swamping)
5. **Author-disjoint splits**: train authors ∩ val authors = ∅; train ∩ test = ∅
6. **De-dup**: MinHash on text 5-grams, drop near-duplicate pairs within 0.85 Jaccard
7. **Length floor/ceiling**: ref_text 200 ≤ len ≤ 4000 chars; target_text 200 ≤ len ≤ 4000 chars
8. **Register balance in val/test**: ≥ 50 pairs per register in val; ≥ 50 in test

## Target output

Final corpus at `/workspace/text-ip-adapter/data/pairs_v2/`:
- `train.v2.jsonl` — target ~30,000–50,000 pairs
- `val.v2.jsonl` — target ~2,000 pairs, balanced per register
- `test.v2.jsonl` — target ~2,000 pairs, balanced per register
- `manifest.json` — source dataset versions, SHA256s, per-register counts, per-author top-100, license attributions
- `README.md` — human summary, caveats, reproduction instructions

## Ingestion structure

All scripts live at `/workspace/text-ip-adapter/scripts/ingest_v2/`:

```
ingest_v2/
  download_pulpo.py         # HF load, filter to English-language for phase 1
  download_un_debate.py     # Harvard Dataverse (requests)
  download_dracor.py        # pydracor API, TEI-XML parse
  download_medium.py        # HF load
  canonicalize.py           # reads raw, writes unified schema to /data/sources_v2/*.jsonl
  make_pairs.py             # pairs same-author docs, applies caps, emits train/val/test
  audit.py                  # validates anti-bias rules, prints report, exits non-zero on violation
  run_all.sh                # orchestration end-to-end
```

## Pair generation rule

For each register, for each author with ≥ 2 documents:
- Sample up to `min(20, C(n, 2))` pairs (ref=doc_i, target=doc_j, i ≠ j, same author)
- Rule-based instruction: `"{verb} {register}-form piece about {topic_a} and {topic_b}"` where topics come from target_text nouns excluding stopwords/markers.

Haiku-cleanup pass after ingest replaces these with natural instructions.

## Budget

- Runtime: 2–4 hrs on pod CPU (dataset downloads + parsing). No GPU needed for ingest.
- Disk: ≤ 30 GB raw on `/workspace`; ≤ 2 GB final corpus.
- Cost: ~$0 for downloads + pod idle. Haiku cleanup via Agent fan-out (subscription), not API billed.

## Escalation

If the subagent hits:
- Auth/403 errors → skip that dataset, continue
- Disk > 30 GB → stop, clean staging, report
- Ingest takes > 5 hrs → checkpoint what's done, report
- Fewer than 2000 unique refs achieved → report and wait for decision before pair generation
