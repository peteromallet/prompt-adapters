#!/usr/bin/env python3
"""Download UN General Debate Corpus from Harvard Dataverse.
File ID 13591895 = UNGDC_1946-2025.tar.gz
Contains per-year per-country plain text files.
"""
import json, re, hashlib, sys, requests, tarfile, io, os
from pathlib import Path

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/un_debate")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/speech.jsonl")
LOG = RAW_DIR / "download.log"

TAR_URL = "https://dataverse.harvard.edu/api/access/datafile/13591895"
TAR_PATH = RAW_DIR / "UNGDC_1946-2025.tar.gz"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def parse_filename(fname):
    """Parse UN debate filename like 'AFG_1946.txt' -> (country, year)."""
    base = os.path.basename(fname)
    m = re.match(r'^([A-Z]{2,4})_(\d{4})\.txt$', base)
    if m:
        return m.group(1), m.group(2)
    return None, None

def split_speech_chunks(text, min_len=200, max_len=4000):
    """Split long speech into chunks. Each chunk = one paragraph or group."""
    # Split by double newline (paragraphs)
    paras = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""

    for para in paras:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < max_len:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if len(current) >= min_len:
                chunks.append(current)
            current = para

    if len(current) >= min_len:
        chunks.append(current)

    # If no chunks (e.g. one giant blob), truncate
    if not chunks and len(text) >= min_len:
        trunc = text[:max_len]
        last_period = trunc.rfind('.')
        if last_period > min_len:
            trunc = trunc[:last_period+1]
        chunks.append(trunc)

    # Cap chunk length
    final = []
    for chunk in chunks:
        if len(chunk) > max_len:
            trunc = chunk[:max_len]
            last_period = trunc.rfind('.')
            if last_period > min_len:
                trunc = trunc[:last_period+1]
            final.append(trunc)
        else:
            final.append(chunk)

    return final

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Download tar if not present
    if not TAR_PATH.exists():
        print(f"Downloading UN General Debate Corpus tar.gz...", flush=True)
        try:
            r = requests.get(TAR_URL, timeout=300, stream=True)
            if r.status_code == 200:
                total = 0
                with open(TAR_PATH, "wb") as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
                        total += len(chunk)
                print(f"Downloaded: {total/1e6:.1f} MB", flush=True)
            else:
                print(f"HTTP {r.status_code} downloading tar.gz", flush=True)
                # Try alternate: the xlsx speakers file for metadata, and README
                # Fall through to HF fallback
        except Exception as e:
            print(f"Tar download failed: {e}", flush=True)
    else:
        print(f"Tar already exists: {TAR_PATH}", flush=True)

    count = 0
    skipped = 0
    seen_ids = set()

    if TAR_PATH.exists() and TAR_PATH.stat().st_size > 1000:
        print("Parsing tar.gz...", flush=True)
        try:
            with tarfile.open(TAR_PATH, "r:gz") as tar, \
                 open(OUT, "w", encoding="utf-8") as fout:
                for member in tar.getmembers():
                    fname = member.name
                    if not fname.endswith(".txt"):
                        continue

                    country, year = parse_filename(fname)
                    if not country or not year:
                        skipped += 1
                        continue

                    try:
                        f = tar.extractfile(member)
                        if f is None:
                            skipped += 1
                            continue
                        raw = f.read().decode("utf-8", errors="replace")
                    except Exception:
                        skipped += 1
                        continue

                    # Use country code as author (each country has speeches across years)
                    author_slug = slug(country)
                    chunks = split_speech_chunks(raw)

                    for chunk in chunks:
                        did = doc_id(author_slug, chunk)
                        if did in seen_ids:
                            continue
                        seen_ids.add(did)

                        record = {
                            "register": "speech",
                            "author": author_slug,
                            "source_dataset": "un_debate",
                            "doc_id": did,
                            "text": chunk,
                            "metadata": {
                                "era": year,
                                "language": "en",
                                "country": country,
                                "genre": "diplomatic_speech",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1

                    if count % 1000 == 0 and count > 0:
                        print(f"  {count} speech chunks...", flush=True)

        except Exception as e:
            print(f"Tar parse failed: {e}", flush=True)

    else:
        # Fallback: use HF dataset if tar failed
        print("Tar unavailable, trying HuggingFace alternatives...", flush=True)
        from datasets import load_dataset
        for ds_name in ["joelniklaus/un-general-debates", "rcunha/un-general-debates",
                         "eliolio/un-general-debates"]:
            try:
                print(f"Trying {ds_name}...", flush=True)
                ds = load_dataset(ds_name, split="train", streaming=True)
                for row in ds:
                    text = row.get("text") or row.get("speech") or ""
                    country = row.get("country") or row.get("code") or ""
                    year = str(row.get("year") or row.get("session") or "")

                    if not text or not country:
                        skipped += 1; continue

                    author_slug = slug(str(country))
                    chunks = split_speech_chunks(text)
                    for chunk in chunks:
                        did = doc_id(author_slug, chunk)
                        if did in seen_ids:
                            continue
                        seen_ids.add(did)
                        record = {
                            "register": "speech",
                            "author": author_slug,
                            "source_dataset": "un_debate",
                            "doc_id": did,
                            "text": chunk,
                            "metadata": {
                                "era": year[:20],
                                "language": "en",
                                "country": str(country)[:50],
                                "genre": "diplomatic_speech",
                            }
                        }
                        with open(OUT, "a", encoding="utf-8") as fout:
                            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1

                if count > 0:
                    print(f"  {ds_name}: {count} docs", flush=True)
                    break
            except Exception as e:
                print(f"  {ds_name} failed: {e}", flush=True)

        if count == 0:
            # Last resort: create placeholder
            print("All UN debate sources failed, writing empty file", flush=True)
            open(OUT, "w").close()

    print(f"UN Debate: {count} speech chunks, {skipped} skipped -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped}\n")

if __name__ == "__main__":
    main()
