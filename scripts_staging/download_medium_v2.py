#!/usr/bin/env python3
"""Download Medium articles from HuggingFace (fabiochiu/medium-articles or BEE-spoke)."""
import json, re, hashlib, sys, ast
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
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_authors(val):
    """Parse author field which may be a string repr of a list."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(a) for a in val if a]
    if isinstance(val, str):
        val = val.strip()
        if val.startswith('['):
            try:
                lst = ast.literal_eval(val)
                return [str(a) for a in lst if a]
            except:
                pass
        return [val]
    return []

def process_row(row, seen_ids, fout, author_counts):
    text = row.get("text") or row.get("content") or row.get("body") or ""
    title = row.get("title") or ""
    authors_raw = row.get("authors") or row.get("author") or ""
    timestamp = str(row.get("timestamp") or row.get("date") or "")
    tags = str(row.get("tags") or "")

    authors = parse_authors(authors_raw)
    if not authors:
        return False

    text = clean_text(text)
    if not text:
        return False

    # Truncate if needed
    if len(text) > 4000:
        trunc = text[:4000]
        last_period = trunc.rfind('.')
        if last_period > 200:
            text = trunc[:last_period+1]
        else:
            return False
    elif len(text) < 200:
        return False

    # Use first author
    author = authors[0]
    if author.lower() in ("unknown", "anon", "anonymous", "", "nan"):
        return False

    author_slug = slug(author)

    # Cap per author during ingestion
    if author_counts.get(author_slug, 0) >= 300:
        return False
    author_counts[author_slug] = author_counts.get(author_slug, 0) + 1

    did = doc_id(author_slug, text)
    if did in seen_ids:
        return False
    seen_ids.add(did)

    # Extract year from timestamp
    era = ""
    if timestamp:
        m = re.search(r'(\d{4})', timestamp)
        if m:
            era = m.group(1)

    record = {
        "register": "essay",
        "author": author_slug,
        "source_dataset": "medium",
        "doc_id": did,
        "text": text,
        "metadata": {
            "era": era,
            "language": "en",
            "country": "",
            "genre": "essay",
            "title": str(title)[:100],
            "tags": tags[:100],
        }
    }
    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0
    author_counts = {}

    with open(OUT, "w", encoding="utf-8") as fout:
        # Try fabiochiu/medium-articles first (more stable)
        print("Loading fabiochiu/medium-articles...", flush=True)
        try:
            ds = load_dataset("fabiochiu/medium-articles", split="train", streaming=True)
            for row in ds:
                if process_row(row, seen_ids, fout, author_counts):
                    count += 1
                else:
                    skipped += 1

                if count % 5000 == 0 and count > 0:
                    print(f"  {count} essays, {len(author_counts)} authors", flush=True)

                if count >= 80000:
                    print(f"Cap at {count}", flush=True)
                    break

            print(f"  fabiochiu done: {count} docs", flush=True)
        except Exception as e:
            print(f"  fabiochiu failed: {e}", flush=True)

        # If we got enough, stop
        if count >= 30000:
            print(f"Sufficient docs from fabiochiu: {count}", flush=True)
        else:
            # Try BEE-spoke
            print("Loading BEE-spoke-data/medium-articles-en...", flush=True)
            try:
                ds2 = load_dataset("BEE-spoke-data/medium-articles-en", split="train", streaming=True)
                prev = count
                for row in ds2:
                    if process_row(row, seen_ids, fout, author_counts):
                        count += 1
                    else:
                        skipped += 1

                    if count % 5000 == 0 and count > prev:
                        print(f"  {count} essays total", flush=True)

                    if count >= 80000:
                        break

                print(f"  BEE-spoke done: +{count - prev} docs", flush=True)
            except Exception as e:
                print(f"  BEE-spoke failed: {e}", flush=True)

    print(f"Medium/Essay: {count} docs, {skipped} skipped, {len(author_counts)} authors -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} unique_authors={len(author_counts)}\n")

if __name__ == "__main__":
    main()
