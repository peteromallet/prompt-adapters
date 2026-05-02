#!/usr/bin/env python3
"""Download poetry from multiple HuggingFace datasets with author info.
Primary: matthh/gutenberg-poetry-corpus, DanFosing/public-domain-poetry, shahules786/PoetryFoundationData
"""
import json, re, hashlib, sys
from pathlib import Path
from datasets import load_dataset
from collections import defaultdict

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/pulpo")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/poetry.jsonl")
LOG = RAW_DIR / "download.log"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def clean_text(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def process_and_write(fout, text, author, seen_ids, author_counts,
                      era="", country="", genre="poetry", source="pulpo",
                      max_per_author=200):
    """Process a single poem and write to output. Returns True if written."""
    text = clean_text(text)
    if not text or not author:
        return False
    if author.lower() in ("unknown", "anon", "anonymous", "", "nan", "none"):
        return False

    if not (200 <= len(text) <= 4000):
        # Try to use if text is just slightly too long
        if len(text) > 4000:
            trunc = text[:4000]
            lp = trunc.rfind('\n')
            if lp > 200:
                text = trunc[:lp]
            else:
                return False
        else:
            return False

    author_slug = slug(str(author))
    if author_counts[author_slug] >= max_per_author:
        return False

    did = doc_id(author_slug, text)
    if did in seen_ids:
        return False

    seen_ids.add(did)
    author_counts[author_slug] += 1

    record = {
        "register": "poetry",
        "author": author_slug,
        "source_dataset": source,
        "doc_id": did,
        "text": text,
        "metadata": {
            "era": str(era)[:50],
            "language": "en",
            "country": str(country)[:50],
            "genre": genre,
        }
    }
    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0
    author_counts = defaultdict(int)

    with open(OUT, "w", encoding="utf-8") as fout:

        # Dataset 1: matthh/gutenberg-poetry-corpus — has author, content, title, author_birth
        print("Loading matthh/gutenberg-poetry-corpus...", flush=True)
        try:
            ds = load_dataset("matthh/gutenberg-poetry-corpus", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                text = row.get("content") or ""
                author = row.get("author") or ""
                era = str(row.get("author_birth") or "")
                if process_and_write(fout, text, author, seen_ids, author_counts,
                                     era=era, genre="poetry", max_per_author=300):
                    count += 1; ds_count += 1
                else:
                    skipped += 1

                if ds_count % 1000 == 0 and ds_count > 0:
                    print(f"  gutenberg-poetry: {ds_count} docs", flush=True)

            print(f"  matthh/gutenberg-poetry-corpus: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  matthh/gutenberg-poetry-corpus failed: {e}", flush=True)

        # Dataset 2: DanFosing/public-domain-poetry — has Author, Title, text
        print("Loading DanFosing/public-domain-poetry...", flush=True)
        try:
            ds = load_dataset("DanFosing/public-domain-poetry", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                text = row.get("text") or ""
                author = row.get("Author") or row.get("author") or ""
                if process_and_write(fout, text, author, seen_ids, author_counts,
                                     genre="poetry", max_per_author=300):
                    count += 1; ds_count += 1
                else:
                    skipped += 1

            print(f"  DanFosing/public-domain-poetry: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  DanFosing/public-domain-poetry failed: {e}", flush=True)

        # Dataset 3: shahules786/PoetryFoundationData — has author, content, age, type
        print("Loading shahules786/PoetryFoundationData...", flush=True)
        try:
            ds = load_dataset("shahules786/PoetryFoundationData", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                text = row.get("content") or row.get("poem") or ""
                author = row.get("author") or ""
                era = row.get("age") or ""
                genre = row.get("type") or "poetry"
                if process_and_write(fout, text, author, seen_ids, author_counts,
                                     era=era, genre=genre, max_per_author=300):
                    count += 1; ds_count += 1
                else:
                    skipped += 1

            print(f"  shahules786/PoetryFoundationData: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  shahules786/PoetryFoundationData failed: {e}", flush=True)

        # Dataset 4: merve/poetry (already run but small)
        print("Loading merve/poetry...", flush=True)
        try:
            ds = load_dataset("merve/poetry", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                text = row.get("content") or ""
                author = row.get("author") or ""
                era = row.get("age") or ""
                genre = row.get("type") or "poetry"
                if process_and_write(fout, text, author, seen_ids, author_counts,
                                     era=era, genre=genre, max_per_author=300):
                    count += 1; ds_count += 1
                else:
                    skipped += 1

            print(f"  merve/poetry: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  merve/poetry failed: {e}", flush=True)

        # Dataset 5: isaacrehg/poetry-instructions
        print("Trying isaacrehg/poetry-instructions...", flush=True)
        try:
            ds = load_dataset("isaacrehg/poetry-instructions", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                if ds_count == 0:
                    print(f"  keys: {list(row.keys())}", flush=True)
                text = row.get("poem") or row.get("text") or row.get("content") or ""
                author = row.get("author") or row.get("poet") or ""
                if process_and_write(fout, text, author, seen_ids, author_counts,
                                     genre="poetry", max_per_author=300):
                    count += 1; ds_count += 1
                else:
                    skipped += 1

            print(f"  isaacrehg/poetry-instructions: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  isaacrehg/poetry-instructions failed: {e}", flush=True)

    print(f"TOTAL poetry: {count} docs, {skipped} skipped, {len(author_counts)} authors -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} unique_authors={len(author_counts)}\n")

if __name__ == "__main__":
    main()
