#!/usr/bin/env python3
"""Download poetry datasets from HuggingFace - uses merve/poetry (has author field).
Falls back to additional datasets for volume.
"""
import json, re, hashlib, sys
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

def clean_text(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0

    with open(OUT, "w", encoding="utf-8") as fout:

        # Dataset 1: merve/poetry — has author, content, age, type
        print("Loading merve/poetry...", flush=True)
        try:
            ds = load_dataset("merve/poetry", split="train", streaming=True)
            for row in ds:
                try:
                    text = clean_text(row.get("content") or "")
                    author = row.get("author") or ""
                    age = row.get("age") or ""
                    ptype = row.get("type") or ""

                    if not text or not author:
                        skipped += 1; continue
                    if author.lower() in ("unknown", "anon", "anonymous"):
                        skipped += 1; continue
                    if not (200 <= len(text) <= 4000):
                        skipped += 1; continue

                    author_slug = slug(str(author))
                    did = doc_id(author_slug, text)
                    if did in seen_ids:
                        skipped += 1; continue
                    seen_ids.add(did)

                    record = {
                        "register": "poetry",
                        "author": author_slug,
                        "source_dataset": "pulpo",
                        "doc_id": did,
                        "text": text,
                        "metadata": {
                            "era": str(age)[:50],
                            "language": "en",
                            "country": "",
                            "genre": str(ptype)[:50] or "poetry",
                        }
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                except Exception:
                    skipped += 1
            print(f"  merve/poetry: +{count} docs", flush=True)
        except Exception as e:
            print(f"  merve/poetry failed: {e}", flush=True)

        # Dataset 2: Ozziey/poetry_dataset — another poetry dataset with authors
        prev_count = count
        print("Loading Ozziey/poetry_dataset...", flush=True)
        try:
            ds2 = load_dataset("Ozziey/poetry_dataset", split="train", streaming=True)
            for row in ds2:
                try:
                    text = clean_text(row.get("Poem") or row.get("poem") or row.get("text") or "")
                    author = (row.get("Poet") or row.get("Author") or row.get("author") or "")

                    if not text or not author:
                        skipped += 1; continue
                    if author.lower() in ("unknown", "anon", "anonymous"):
                        skipped += 1; continue
                    if not (200 <= len(text) <= 4000):
                        skipped += 1; continue

                    author_slug = slug(str(author))
                    did = doc_id(author_slug, text)
                    if did in seen_ids:
                        skipped += 1; continue
                    seen_ids.add(did)

                    record = {
                        "register": "poetry",
                        "author": author_slug,
                        "source_dataset": "pulpo",
                        "doc_id": did,
                        "text": text,
                        "metadata": {
                            "era": "",
                            "language": "en",
                            "country": "",
                            "genre": "poetry",
                        }
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                except Exception:
                    skipped += 1
            print(f"  Ozziey/poetry_dataset: +{count - prev_count} docs", flush=True)
        except Exception as e:
            print(f"  Ozziey/poetry_dataset failed: {e}", flush=True)

        # Dataset 3: try spencermountain/poets or similar
        prev_count = count
        print("Loading Hersh/poems...", flush=True)
        try:
            ds3 = load_dataset("Hersh/poems", split="train", streaming=True)
            for row in ds3:
                try:
                    # Print first row keys
                    if count == prev_count:
                        print(f"  Hersh/poems keys: {list(row.keys())}", flush=True)
                    text = clean_text(row.get("poem") or row.get("text") or row.get("content") or "")
                    author = (row.get("author") or row.get("poet") or "")

                    if not text or not author:
                        skipped += 1; continue
                    if author.lower() in ("unknown", "anon", "anonymous"):
                        skipped += 1; continue
                    if not (200 <= len(text) <= 4000):
                        skipped += 1; continue

                    author_slug = slug(str(author))
                    did = doc_id(author_slug, text)
                    if did in seen_ids:
                        skipped += 1; continue
                    seen_ids.add(did)

                    record = {
                        "register": "poetry",
                        "author": author_slug,
                        "source_dataset": "pulpo",
                        "doc_id": did,
                        "text": text,
                        "metadata": {
                            "era": "",
                            "language": "en",
                            "country": "",
                            "genre": "poetry",
                        }
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                except Exception:
                    skipped += 1
            print(f"  Hersh/poems: +{count - prev_count} docs", flush=True)
        except Exception as e:
            print(f"  Hersh/poems failed: {e}", flush=True)

        # Dataset 4: try more poetry sources
        prev_count = count
        for ds_name in ["biglam/gutenberg-poetry", "thehrvoje/poetry_dataset_all_authors_english",
                         "sadikali/poetry-dataset"]:
            print(f"Trying {ds_name}...", flush=True)
            try:
                ds4 = load_dataset(ds_name, split="train", streaming=True)
                ds4_count = 0
                for row in ds4:
                    try:
                        if count == prev_count:
                            print(f"  {ds_name} keys: {list(row.keys())}", flush=True)
                        # Try various field names
                        text = ""
                        for tf in ["poem", "text", "content", "poem_text", "body", "Poem"]:
                            if row.get(tf):
                                text = clean_text(str(row[tf]))
                                break
                        author = ""
                        for af in ["author", "poet", "Author", "Poet", "writer"]:
                            if row.get(af):
                                author = str(row[af])
                                break

                        if not text or not author:
                            skipped += 1; continue
                        if author.lower() in ("unknown", "anon", "anonymous"):
                            skipped += 1; continue
                        if not (200 <= len(text) <= 4000):
                            skipped += 1; continue

                        author_slug = slug(author)
                        did = doc_id(author_slug, text)
                        if did in seen_ids:
                            skipped += 1; continue
                        seen_ids.add(did)

                        record = {
                            "register": "poetry",
                            "author": author_slug,
                            "source_dataset": "pulpo",
                            "doc_id": did,
                            "text": text,
                            "metadata": {
                                "era": str(row.get("year") or row.get("age") or "")[:50],
                                "language": "en",
                                "country": str(row.get("country") or "")[:50],
                                "genre": "poetry",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
                        ds4_count += 1
                    except Exception:
                        skipped += 1
                print(f"  {ds_name}: +{ds4_count} docs", flush=True)
            except Exception as e:
                print(f"  {ds_name} failed: {e}", flush=True)

    print(f"TOTAL poetry: {count} docs, {skipped} skipped -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped}\n")

if __name__ == "__main__":
    main()
