#!/usr/bin/env python3
"""Download and canonicalize PULPO (linhd-postdata/pulpo) from HuggingFace.
Filters to English-language poems, groups by author, writes canonical JSONL.
"""
import json, re, hashlib, os, sys
from pathlib import Path
from datasets import load_dataset

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/pulpo")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/poetry.jsonl")
LOG = RAW_DIR / "download.log"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading PULPO from HuggingFace (streaming)...", flush=True)

    # Try anonymous load
    try:
        ds = load_dataset("linhd-postdata/pulpo", split="train", streaming=True,
                          trust_remote_code=True)
    except Exception as e:
        print(f"ERROR loading PULPO: {e}", flush=True)
        sys.exit(1)

    seen_ids = set()
    count = 0
    skipped = 0

    with open(OUT, "w", encoding="utf-8") as fout:
        for row in ds:
            try:
                # Filter to English
                lang = (row.get("language") or row.get("lang") or "").lower()
                if lang and lang not in ("en", "english", "eng"):
                    skipped += 1
                    continue

                text = row.get("poem_text") or row.get("text") or row.get("content") or ""
                author = row.get("author") or row.get("poet") or "unknown"
                if not text or not author or author.lower() in ("unknown", "anon", "anonymous"):
                    skipped += 1
                    continue

                # Length filter
                if not (200 <= len(text) <= 4000):
                    skipped += 1
                    continue

                author_slug = slug(str(author))
                did = doc_id(author_slug, text)
                if did in seen_ids:
                    skipped += 1
                    continue
                seen_ids.add(did)

                # Extract metadata
                era = str(row.get("year") or row.get("date") or "")
                country = str(row.get("country") or row.get("nationality") or "")
                title = str(row.get("title") or "")

                record = {
                    "register": "poetry",
                    "author": author_slug,
                    "source_dataset": "pulpo",
                    "doc_id": did,
                    "text": text,
                    "metadata": {
                        "era": era[:50],
                        "language": "en",
                        "country": country[:50],
                        "genre": "poetry",
                        "title": title[:100],
                    }
                }
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

                if count % 5000 == 0:
                    print(f"  processed {count} poems, skipped {skipped}", flush=True)

                # Cap at 80k docs to stay manageable
                if count >= 80000:
                    print(f"Cap reached at {count}", flush=True)
                    break

            except Exception as e:
                skipped += 1
                continue

    print(f"PULPO: {count} docs written, {skipped} skipped -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped}\n")

if __name__ == "__main__":
    main()
