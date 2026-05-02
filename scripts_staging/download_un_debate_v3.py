#!/usr/bin/env python3
"""Download speech corpus from Eugleo/us-congressional-speeches (HuggingFace).
Falls back to ibm-research/debate_speeches.
The Harvard Dataverse UN debate corpus requires guestbook sign-in (skipped per spec).
"""
import json, re, hashlib, sys
from pathlib import Path
from datasets import load_dataset
from collections import defaultdict

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/un_debate")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/speech.jsonl")
LOG = RAW_DIR / "download.log"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0
    author_counts = defaultdict(int)
    sources_used = []

    with open(OUT, "w", encoding="utf-8") as fout:

        # Primary: US Congressional Speeches (has named speakers, dates)
        print("Loading Eugleo/us-congressional-speeches...", flush=True)
        try:
            ds = load_dataset("Eugleo/us-congressional-speeches", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                try:
                    text = clean_text(row.get("text") or "")
                    first = row.get("first_name") or ""
                    last = row.get("last_name") or ""
                    speaker = row.get("speaker") or f"{first} {last}".strip()
                    if not speaker:
                        skipped += 1; continue
                    date = str(row.get("date") or "")
                    state = str(row.get("state") or "")

                    if not text or not speaker:
                        skipped += 1; continue
                    if speaker.lower() in ("unknown", "anon", "", "nan"):
                        skipped += 1; continue

                    if not (200 <= len(text) <= 4000):
                        if len(text) > 4000:
                            trunc = text[:4000]
                            lp = trunc.rfind('.')
                            if lp > 200:
                                text = trunc[:lp+1]
                            else:
                                skipped += 1; continue
                        else:
                            skipped += 1; continue

                    author_slug = slug(speaker)

                    # Per-author cap
                    if author_counts[author_slug] >= 200:
                        skipped += 1; continue
                    author_counts[author_slug] += 1

                    did = doc_id(author_slug, text)
                    if did in seen_ids:
                        skipped += 1; continue
                    seen_ids.add(did)

                    # Extract year
                    era = ""
                    if date:
                        m = re.search(r'(\d{4})', date)
                        if m:
                            era = m.group(1)

                    record = {
                        "register": "speech",
                        "author": author_slug,
                        "source_dataset": "un_debate",
                        "doc_id": did,
                        "text": text,
                        "metadata": {
                            "era": era,
                            "language": "en",
                            "country": f"US/{state}" if state else "US",
                            "genre": "political_speech",
                        }
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                    ds_count += 1

                    if count % 5000 == 0:
                        print(f"  {count} speeches, {len(author_counts)} speakers", flush=True)

                    if count >= 60000:
                        print(f"Cap at {count}", flush=True)
                        break

                except Exception:
                    skipped += 1
                    continue

            print(f"  us-congressional: {ds_count} docs", flush=True)
            sources_used.append(f"Eugleo/us-congressional-speeches ({ds_count})")

        except Exception as e:
            print(f"  us-congressional failed: {e}", flush=True)

        # Supplement with MEPs speeches (European Parliament)
        if count < 20000:
            print("Loading misclassified/meps_speeches...", flush=True)
            try:
                ds2 = load_dataset("misclassified/meps_speeches", split="train", streaming=True)
                ds_count2 = 0
                for row in ds2:
                    try:
                        text = clean_text(row.get("Content") or "")
                        speaker = row.get("MP") or ""
                        date = str(row.get("Date") or "")
                        lang = str(row.get("Language") or "").upper()
                        country = str(row.get("country") or "")

                        if lang not in ("EN", ""):
                            skipped += 1; continue

                        if not text or not speaker:
                            skipped += 1; continue

                        if not (200 <= len(text) <= 4000):
                            if len(text) > 4000:
                                trunc = text[:4000]
                                lp = trunc.rfind('.')
                                if lp > 200:
                                    text = trunc[:lp+1]
                                else:
                                    skipped += 1; continue
                            else:
                                skipped += 1; continue

                        author_slug = slug(speaker)
                        if author_counts[author_slug] >= 200:
                            skipped += 1; continue
                        author_counts[author_slug] += 1

                        did = doc_id(author_slug, text)
                        if did in seen_ids:
                            skipped += 1; continue
                        seen_ids.add(did)

                        era = ""
                        if date:
                            m = re.search(r'(\d{4})', date)
                            if m:
                                era = m.group(1)

                        record = {
                            "register": "speech",
                            "author": author_slug,
                            "source_dataset": "un_debate",
                            "doc_id": did,
                            "text": text,
                            "metadata": {
                                "era": era,
                                "language": "en",
                                "country": country,
                                "genre": "parliamentary_speech",
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
                        ds_count2 += 1

                    except Exception:
                        skipped += 1

                print(f"  meps: {ds_count2} docs", flush=True)
                sources_used.append(f"misclassified/meps_speeches ({ds_count2})")

            except Exception as e:
                print(f"  meps failed: {e}", flush=True)

    print(f"Speech total: {count} docs, {skipped} skipped, {len(author_counts)} speakers -> {OUT}", flush=True)
    print(f"Sources: {sources_used}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} unique_authors={len(author_counts)}\n")
        f.write(f"Note: Harvard Dataverse UN debate requires guestbook auth - SKIPPED per spec\n")
        f.write(f"Sources used: {sources_used}\n")

if __name__ == "__main__":
    main()
