#!/usr/bin/env python3
"""Download UN General Debate Corpus from Harvard Dataverse and canonicalize.
DOI: 10.7910/DVN/0TJX8Y
Uses the direct CSV download (public domain).
"""
import json, re, hashlib, os, sys, requests, zipfile, io
from pathlib import Path

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/un_debate")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/speech.jsonl")
LOG = RAW_DIR / "download.log"

# Harvard Dataverse direct file access
DATAVERSE_BASE = "https://dataverse.harvard.edu"
DATASET_DOI = "doi:10.7910/DVN/0TJX8Y"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def try_download_csv():
    """Try to get the CSV via Dataverse API."""
    # Try the search API first
    search_url = f"{DATAVERSE_BASE}/api/datasets/:persistentId/?persistentId={DATASET_DOI}"
    try:
        r = requests.get(search_url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            files = data.get("data", {}).get("latestVersion", {}).get("files", [])
            for f in files:
                fname = f.get("dataFile", {}).get("filename", "")
                if fname.endswith(".csv") or fname.endswith(".tab"):
                    fid = f.get("dataFile", {}).get("id")
                    if fid:
                        return fid, fname
    except Exception as e:
        print(f"API search failed: {e}")
    return None, None

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("Attempting UN Debate Corpus download from Harvard Dataverse...", flush=True)

    # Try to get file list
    fid, fname = try_download_csv()
    csv_path = RAW_DIR / "un-general-debates.csv"

    if not csv_path.exists():
        if fid:
            dl_url = f"{DATAVERSE_BASE}/api/access/datafile/{fid}"
            print(f"Downloading file id={fid} ({fname})...", flush=True)
            try:
                r = requests.get(dl_url, timeout=120, stream=True)
                if r.status_code == 200:
                    with open(csv_path, "wb") as f:
                        for chunk in r.iter_content(65536):
                            f.write(chunk)
                    print(f"Downloaded: {csv_path.stat().st_size} bytes", flush=True)
                else:
                    print(f"HTTP {r.status_code} on download, trying alternate...", flush=True)
                    fid = None
            except Exception as e:
                print(f"Download failed: {e}", flush=True)
                fid = None

        if not fid or not csv_path.exists():
            # Try alternate direct URL (known working link from Harvard Dataverse)
            alt_urls = [
                "https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/0TJX8Y/MEBYAT",
                "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/0TJX8Y",
            ]
            for url in alt_urls:
                try:
                    print(f"Trying: {url}", flush=True)
                    r = requests.get(url, timeout=120, stream=True, allow_redirects=True)
                    if r.status_code == 200 and len(r.content) > 1000:
                        with open(RAW_DIR / "un_dataset_bundle.bin", "wb") as f:
                            f.write(r.content)
                        print(f"Got {len(r.content)} bytes", flush=True)
                        break
                except Exception as e:
                    print(f"  Failed: {e}", flush=True)

    # Parse CSV if available
    if csv_path.exists():
        import csv
        print("Parsing CSV...", flush=True)
        count = 0
        skipped = 0
        seen_ids = set()

        with open(OUT, "w", encoding="utf-8") as fout, \
             open(csv_path, "r", encoding="utf-8", errors="replace") as fin:
            reader = csv.DictReader(fin)
            for row in reader:
                try:
                    text = row.get("text", "") or row.get("speech", "") or ""
                    country = row.get("country", "") or row.get("country_name", "")
                    speaker = row.get("speaker", "") or row.get("name", "")
                    year = row.get("year", "") or row.get("session", "")

                    # If no speaker, use country as author
                    author = speaker if speaker and speaker.lower() not in ("nan", "", "unknown") else country

                    if not text or not author:
                        skipped += 1
                        continue
                    if not (200 <= len(text) <= 4000):
                        skipped += 1
                        continue

                    author_slug = slug(str(author))
                    did = doc_id(author_slug, text)
                    if did in seen_ids:
                        skipped += 1
                        continue
                    seen_ids.add(did)

                    record = {
                        "register": "speech",
                        "author": author_slug,
                        "source_dataset": "un_debate",
                        "doc_id": did,
                        "text": text,
                        "metadata": {
                            "era": str(year)[:20],
                            "language": "en",
                            "country": str(country)[:50],
                            "genre": "diplomatic_speech",
                        }
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1

                    if count % 1000 == 0:
                        print(f"  {count} speeches...", flush=True)

                except Exception as e:
                    skipped += 1
                    continue

        print(f"UN Debate: {count} docs written, {skipped} skipped -> {OUT}", flush=True)
        with open(LOG, "w") as f:
            f.write(f"count={count} skipped={skipped}\n")
    else:
        # Try HuggingFace mirror
        print("CSV not available, trying HuggingFace mirror...", flush=True)
        try:
            from datasets import load_dataset
            ds = load_dataset("Eugleo/un-general-debates", split="train", trust_remote_code=True)
            count = 0
            skipped = 0
            seen_ids = set()

            with open(OUT, "w", encoding="utf-8") as fout:
                for row in ds:
                    try:
                        text = row.get("text", "") or row.get("speech", "")
                        country = row.get("country", "")
                        year = str(row.get("year", ""))

                        author = country  # country as author for UN debates
                        if not text or not author:
                            skipped += 1
                            continue
                        if not (200 <= len(text) <= 4000):
                            skipped += 1
                            continue

                        author_slug = slug(str(author))
                        did = doc_id(author_slug, text)
                        if did in seen_ids:
                            skipped += 1
                            continue
                        seen_ids.add(did)

                        record = {
                            "register": "speech",
                            "author": author_slug,
                            "source_dataset": "un_debate",
                            "doc_id": did,
                            "text": text,
                            "metadata": {
                                "era": year[:20],
                                "language": "en",
                                "country": str(country)[:50],
                                "genre": "diplomatic_speech",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1

                    except Exception:
                        skipped += 1
                        continue

            print(f"UN Debate (HF): {count} docs, {skipped} skipped -> {OUT}", flush=True)
            with open(LOG, "w") as f:
                f.write(f"source=huggingface count={count} skipped={skipped}\n")

        except Exception as e:
            print(f"HF fallback also failed: {e}", flush=True)
            # Write empty file so pipeline continues
            open(OUT, "w").close()
            with open(LOG, "w") as f:
                f.write(f"SKIPPED: {e}\n")

if __name__ == "__main__":
    main()
