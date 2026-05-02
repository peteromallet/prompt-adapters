#!/usr/bin/env python3
"""Download DraCor plays via REST API and split into scene/act chunks for pairing.
Includes English corpus (shake) + English-translated plays where available.
Also ingests additional drama sources from HuggingFace.
"""
import json, re, hashlib, sys, time, requests
from pathlib import Path
from collections import defaultdict

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/dracor")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/screenplay.jsonl")
LOG = RAW_DIR / "download.log"

BASE = "https://dracor.org/api/v1"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def get_play_text(corpus_name, play_name):
    url = f"{BASE}/corpora/{corpus_name}/plays/{play_name}/spoken-text"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and r.text.strip():
            return r.text
    except Exception:
        pass
    return None

def split_into_chunks(text, min_len=200, max_len=4000):
    """Split play text into multiple chunks of varying granularity."""
    chunks = []

    # Try scene-level splits first (most granular)
    scene_pattern = r'\n(?:SCENE|Scene|ACT|Act|EPISODE|Episode|PROLOGUE|EPILOGUE|CHORUS)\s+[IVXivx\d\w]'
    parts = re.split(scene_pattern, text)

    if len(parts) > 1:
        for part in parts:
            part = part.strip()
            if len(part) >= min_len and len(part) <= max_len:
                chunks.append(part)
            elif len(part) > max_len:
                # Chop into paragraphs
                paras = re.split(r'\n\s*\n', part)
                current = ""
                for para in paras:
                    para = para.strip()
                    if not para:
                        continue
                    if len(current) + len(para) + 2 <= max_len:
                        current = (current + "\n\n" + para).strip() if current else para
                    else:
                        if len(current) >= min_len:
                            chunks.append(current)
                        current = para
                if len(current) >= min_len:
                    chunks.append(current)
    else:
        # No scene markers - split by paragraph groups
        paras = re.split(r'\n\s*\n', text)
        current = ""
        for para in paras:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= max_len:
                current = (current + "\n\n" + para).strip() if current else para
            else:
                if len(current) >= min_len:
                    chunks.append(current)
                current = para
        if len(current) >= min_len:
            chunks.append(current)

    # Filter and cap
    final = []
    for c in chunks:
        c = c.strip()
        if min_len <= len(c) <= max_len:
            final.append(c)
        elif len(c) > max_len:
            trunc = c[:max_len]
            lp = trunc.rfind('.')
            if lp > min_len:
                final.append(trunc[:lp+1])

    return final

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    seen_ids = set()
    count = 0
    skipped = 0
    plays_fetched = 0

    with open(OUT, "w", encoding="utf-8") as fout:

        # 1. DraCor REST API - Shakespeare (shake corpus)
        print("Fetching DraCor shake corpus...", flush=True)
        try:
            r = requests.get(f"{BASE}/corpora/shake", timeout=30)
            if r.status_code == 200:
                plays = r.json().get("plays", [])
                print(f"  shake: {len(plays)} plays", flush=True)
                for play in plays:
                    play_id = play.get("name") or ""
                    title = play.get("title") or ""
                    authors = play.get("authors") or []
                    author_name = authors[0].get("name") if authors else "Shakespeare, William"
                    author_slug = slug(author_name)
                    year = str(play.get("yearNormalized") or play.get("writtenYear") or "1600")

                    text = get_play_text("shake", play_id)
                    if not text:
                        skipped += 1
                        continue

                    plays_fetched += 1
                    chunks = split_into_chunks(text)

                    for chunk in chunks:
                        did = doc_id(author_slug, chunk)
                        if did in seen_ids:
                            continue
                        seen_ids.add(did)
                        record = {
                            "register": "screenplay",
                            "author": author_slug,
                            "source_dataset": "dracor",
                            "doc_id": did,
                            "text": chunk,
                            "metadata": {
                                "era": year[:20],
                                "language": "en",
                                "country": "UK",
                                "genre": "play",
                                "title": str(title)[:100],
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1

                    time.sleep(0.1)
                print(f"  shake done: {count} chunks from {plays_fetched} plays", flush=True)
        except Exception as e:
            print(f"  shake failed: {e}", flush=True)

        # 2. HuggingFace drama datasets
        from datasets import load_dataset

        hf_drama_datasets = [
            ("jusidmh/shakespeare-gutenberg", {"text_field": "text", "author_field": None, "fixed_author": "shakespeare_william", "era": "1600", "country": "UK"}),
            ("NebulaeWis/william-shakespeare-poems-and-plays", {"text_field": "text", "author_field": None, "fixed_author": "shakespeare_william", "era": "1600", "country": "UK"}),
        ]

        for ds_name, cfg in hf_drama_datasets:
            print(f"Trying HF drama dataset: {ds_name}...", flush=True)
            try:
                ds = load_dataset(ds_name, split="train", streaming=True)
                ds_count = 0
                for row in ds:
                    if count == 0:
                        print(f"  {ds_name} keys: {list(row.keys())}", flush=True)

                    text = ""
                    for tf in [cfg.get("text_field", "text"), "text", "content", "body", "dialogue"]:
                        if row.get(tf):
                            text = str(row[tf]).strip()
                            break

                    if cfg.get("fixed_author"):
                        author_slug = cfg["fixed_author"]
                    else:
                        author = row.get(cfg.get("author_field", "author")) or ""
                        if not author:
                            skipped += 1; continue
                        author_slug = slug(str(author))

                    chunks = split_into_chunks(text) if text else []
                    for chunk in chunks:
                        did = doc_id(author_slug, chunk)
                        if did in seen_ids:
                            continue
                        seen_ids.add(did)
                        record = {
                            "register": "screenplay",
                            "author": author_slug,
                            "source_dataset": "dracor",
                            "doc_id": did,
                            "text": chunk,
                            "metadata": {
                                "era": cfg.get("era", ""),
                                "language": "en",
                                "country": cfg.get("country", ""),
                                "genre": "play",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
                        ds_count += 1

                print(f"  {ds_name}: +{ds_count} docs", flush=True)
            except Exception as e:
                print(f"  {ds_name} failed: {e}", flush=True)

        # 3. Try Project Gutenberg drama via HF
        print("Trying Gutenberg drama sources...", flush=True)
        for ds_name in ["storytracer/Project-Gutenberg-Books-en",
                         "deepmind/gutenberg_fiction_en"]:
            print(f"Trying {ds_name}...", flush=True)
            try:
                ds = load_dataset(ds_name, split="train", streaming=True)
                ds_count = 0
                for row in ds:
                    # Get subject/genre to filter to plays
                    subject = str(row.get("subject") or row.get("genre") or row.get("tags") or "").lower()
                    if not any(k in subject for k in ["drama", "play", "theatre", "comedy", "tragedy"]):
                        continue

                    text = ""
                    for tf in ["text", "content", "body"]:
                        if row.get(tf):
                            text = str(row[tf]).strip()
                            break
                    if not text:
                        continue

                    author = str(row.get("author") or row.get("writer") or "")
                    if not author or author.lower() in ("unknown", ""):
                        continue

                    author_slug = slug(author)
                    era = str(row.get("year") or row.get("publication_date") or "")[:20]
                    chunks = split_into_chunks(text)
                    for chunk in chunks:
                        did = doc_id(author_slug, chunk)
                        if did in seen_ids:
                            continue
                        seen_ids.add(did)
                        record = {
                            "register": "screenplay",
                            "author": author_slug,
                            "source_dataset": "dracor",
                            "doc_id": did,
                            "text": chunk,
                            "metadata": {
                                "era": era,
                                "language": "en",
                                "country": "",
                                "genre": "play",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
                        ds_count += 1

                    if ds_count >= 2000:
                        break

                print(f"  {ds_name}: +{ds_count} docs", flush=True)
                if ds_count > 0:
                    break
            except Exception as e:
                print(f"  {ds_name} failed: {e}", flush=True)

    print(f"DraCor total: {count} docs, {skipped} skipped -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} plays_fetched={plays_fetched}\n")

if __name__ == "__main__":
    main()
