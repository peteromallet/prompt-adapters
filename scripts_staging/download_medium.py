#!/usr/bin/env python3
"""Download BEE-spoke-data/medium-articles-en from HuggingFace and canonicalize.
Groups by author, filters length, deduplicates.
"""
import json, re, hashlib, sys
from pathlib import Path
from datasets import load_dataset

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/medium")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/essay.jsonl")
LOG = RAW_DIR / "download.log"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def clean_text(text):
    """Basic cleaning: remove excess whitespace, html artifacts."""
    text = re.sub(r'<[^>]+>', ' ', text)  # strip HTML tags
    text = re.sub(r'http\S+', '', text)   # remove URLs
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading Medium articles from HuggingFace (streaming)...", flush=True)

    try:
        ds = load_dataset("BEE-spoke-data/medium-articles-en", split="train",
                          streaming=True, trust_remote_code=True)
    except Exception as e:
        print(f"ERROR loading medium-articles-en: {e}", flush=True)
        # Try fallback dataset name
        try:
            ds = load_dataset("fabiochiu/medium-articles", split="train",
                              streaming=True, trust_remote_code=True)
            print("Using fallback: fabiochiu/medium-articles", flush=True)
        except Exception as e2:
            print(f"Fallback also failed: {e2}", flush=True)
            open(OUT, "w").close()
            with open(LOG, "w") as f:
                f.write(f"SKIPPED: {e} / {e2}\n")
            sys.exit(0)

    seen_ids = set()
    count = 0
    skipped = 0
    author_counts = {}

    with open(OUT, "w", encoding="utf-8") as fout:
        for row in ds:
            try:
                text = row.get("text") or row.get("content") or row.get("body") or ""
                author = row.get("author") or row.get("authors") or ""
                if isinstance(author, list):
                    author = author[0] if author else ""
                title = row.get("title") or ""
                pub = row.get("publication") or row.get("tag") or ""

                if not text or not author:
                    skipped += 1
                    continue
                if author.lower() in ("unknown", "anon", "anonymous", "", "nan"):
                    skipped += 1
                    continue

                text = clean_text(text)
                if not (200 <= len(text) <= 4000):
                    # If too long, try to use first 4000 chars snapped to sentence
                    if len(text) > 4000:
                        trunc = text[:4000]
                        last_period = trunc.rfind('.')
                        if last_period > 200:
                            text = trunc[:last_period+1]
                        else:
                            skipped += 1
                            continue
                    else:
                        skipped += 1
                        continue

                author_slug = slug(str(author))

                # Per-author cap at 500 docs during ingestion (pairs gen applies harder cap)
                if author_counts.get(author_slug, 0) >= 500:
                    skipped += 1
                    continue
                author_counts[author_slug] = author_counts.get(author_slug, 0) + 1

                did = doc_id(author_slug, text)
                if did in seen_ids:
                    skipped += 1
                    continue
                seen_ids.add(did)

                record = {
                    "register": "essay",
                    "author": author_slug,
                    "source_dataset": "medium",
                    "doc_id": did,
                    "text": text,
                    "metadata": {
                        "era": "",
                        "language": "en",
                        "country": "",
                        "genre": "essay",
                        "title": str(title)[:100],
                        "publication": str(pub)[:100],
                    }
                }
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

                if count % 5000 == 0:
                    print(f"  {count} articles, {skipped} skipped, {len(author_counts)} unique authors", flush=True)

                # Cap at 100k docs total
                if count >= 100000:
                    print(f"Cap at {count}", flush=True)
                    break

            except Exception as e:
                skipped += 1
                continue

    print(f"Medium: {count} docs, {skipped} skipped, {len(author_counts)} authors -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} unique_authors={len(author_counts)}\n")

if __name__ == "__main__":
    main()
