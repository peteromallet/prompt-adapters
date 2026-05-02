#!/usr/bin/env python3
"""Generate manifest.json and README.md for the v2 corpus."""
import json, hashlib, datetime
from pathlib import Path
from collections import defaultdict

PAIRS_DIR = Path("/workspace/text-ip-adapter/data/pairs_v2")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def count_pairs(path):
    n = 0
    if path.exists():
        with open(path) as f:
            for line in f:
                if line.strip():
                    n += 1
    return n

def main():
    files = {
        "train.v2.jsonl": PAIRS_DIR / "train.v2.jsonl",
        "val.v2.jsonl": PAIRS_DIR / "val.v2.jsonl",
        "test.v2.jsonl": PAIRS_DIR / "test.v2.jsonl",
    }

    file_stats = {}
    for name, path in files.items():
        if path.exists():
            file_stats[name] = {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "pairs": count_pairs(path),
            }

    # Load pair stats if available
    pair_stats = {}
    stats_path = PAIRS_DIR / "pair_stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            pair_stats = json.load(f)

    # Load audit report if available
    audit = {}
    audit_path = PAIRS_DIR / "audit_report.json"
    if audit_path.exists():
        with open(audit_path) as f:
            audit = json.load(f)

    # Collect per-register doc counts from canonical files
    canonical_dir = Path("/workspace/text-ip-adapter/data/sources_v2/canonical")
    canonical_stats = {}
    for reg in ["poetry", "speech", "screenplay", "essay"]:
        path = canonical_dir / f"{reg}.jsonl"
        if path.exists():
            n = 0
            authors = set()
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            doc = json.loads(line)
                            n += 1
                            authors.add(doc.get("author", ""))
                        except:
                            pass
            canonical_stats[reg] = {"docs": n, "unique_authors": len(authors)}

    manifest = {
        "corpus_version": "v2",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "schema_version": "1.0",
        "sources": {
            "pulpo": {
                "name": "PULPO (linhd-postdata/pulpo)",
                "license": "CC0",
                "url": "https://huggingface.co/datasets/linhd-postdata/pulpo",
                "register": "poetry",
            },
            "un_debate": {
                "name": "UN General Debate Corpus",
                "license": "Public Domain",
                "url": "https://doi.org/10.7910/DVN/0TJX8Y",
                "register": "speech",
            },
            "dracor": {
                "name": "DraCor",
                "license": "CC-BY 4.0",
                "url": "https://dracor.org",
                "register": "screenplay",
            },
            "medium": {
                "name": "BEE-spoke-data/medium-articles-en",
                "license": "MIT",
                "url": "https://huggingface.co/datasets/BEE-spoke-data/medium-articles-en",
                "register": "essay",
            },
        },
        "canonical_stats": canonical_stats,
        "pair_stats": pair_stats,
        "files": file_stats,
        "anti_bias_caps": {
            "per_author_max_frac": 0.02,
            "per_source_doc_max_frac": 0.005,
            "per_register_max_frac": 0.40,
            "per_source_dataset_max_frac": 0.50,
        },
        "split_method": "author-disjoint 90/5/5",
        "dedup_method": "5-gram Jaccard > 0.85 → skip",
        "length_filter": "200 <= chars <= 4000",
        "audit_violations": audit.get("violations", []),
        "audit_passed": len(audit.get("violations", [])) == 0,
    }

    with open(PAIRS_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"manifest.json written", flush=True)

    # Write README.md
    train_n = file_stats.get("train.v2.jsonl", {}).get("pairs", 0)
    val_n = file_stats.get("val.v2.jsonl", {}).get("pairs", 0)
    test_n = file_stats.get("test.v2.jsonl", {}).get("pairs", 0)

    reg_counts = pair_stats.get("register_counts", {})
    ds_counts = pair_stats.get("dataset_counts", {})

    top10 = pair_stats.get("top10_authors", [])
    top10_str = "\n".join(f"| {a} | {c} | {p}% |" for a, c, p in top10) if top10 else ""

    readme = f"""# text-ip-adapter v2 Training Corpus

Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Summary

| Split | Pairs |
|-------|-------|
| train.v2.jsonl | {train_n:,} |
| val.v2.jsonl | {val_n:,} |
| test.v2.jsonl | {test_n:,} |
| **Total** | **{train_n+val_n+test_n:,}** |

## Registers

| Register | Pairs |
|----------|-------|
{"".join(f"| {r} | {c:,} |" + chr(10) for r, c in reg_counts.items())}

## Source Datasets

| Dataset | Pairs |
|---------|-------|
{"".join(f"| {d} | {c:,} |" + chr(10) for d, c in ds_counts.items())}

## Top-10 Authors by Pair Count

| Author | Pairs | Share |
|--------|-------|-------|
{top10_str}

## Anti-Bias Caps Applied

- Per-author: ≤ 2% of total corpus
- Per-source-doc: ≤ 0.5% of total corpus
- Per-register: ≤ 40% of total corpus
- Per-source-dataset: ≤ 50% of total corpus

## Splits

Author-disjoint: train/val/test authors are fully disjoint.
Ratio: 90% train / 5% val / 5% test (by author count).

## Deduplication

Near-duplicate pairs removed using 5-gram Jaccard similarity > 0.85.

## Schema

```json
{{
  "register": "poetry|speech|screenplay|essay",
  "author": "<slug>",
  "source_dataset": "pulpo|un_debate|dracor|medium",
  "ref_doc_id": "<author_slug>_<8-char hash>",
  "target_doc_id": "<author_slug>_<8-char hash>",
  "ref_text": "...",
  "target_text": "...",
  "instruction": "<rule-based placeholder>",
  "instruction_rule_based": "<same — preserve for haiku rewrite>",
  "metadata": {{
    "era": "...",
    "language": "...",
    "country": "...",
    "genre": "...",
    "instruction_rule_based_topics": [...]
  }}
}}
```

## Reproduction

```bash
cd /workspace/text-ip-adapter/scripts/ingest_v2
python download_pulpo.py
python download_un_debate.py
python download_dracor.py
python download_medium.py
python make_pairs.py
python audit.py
python make_manifest.py
```

## File Checksums (SHA256)

{"".join(f"- {k}: {v['sha256']}" + chr(10) for k, v in file_stats.items())}

## Licenses

- PULPO: CC0 (public domain)
- UN General Debate Corpus: Public Domain
- DraCor: CC-BY 4.0
- Medium Articles: MIT (dataset compilation)
"""

    with open(PAIRS_DIR / "README.md", "w") as f:
        f.write(readme)
    print(f"README.md written", flush=True)

if __name__ == "__main__":
    main()
