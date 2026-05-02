#!/usr/bin/env python3
"""Download screenplay/drama content from multiple sources.
Primary: DraCor REST API (Shakespeare, shake corpus) + chunked by scene
Secondary: alankent/ordinary_screenplays, gutenberg poetry corpus for drama works
"""
import json, re, hashlib, sys, time, requests
from pathlib import Path
from collections import defaultdict
from datasets import load_dataset

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
    """Split play text into multiple scene/act chunks."""
    # Try multiple delimiters
    chunks = []

    # Split by speaker turns grouped into scenes
    # Strategy 1: split by ACT/SCENE markers
    parts = re.split(r'\n(?:ACT|SCENE|Scene|Act|SCENE |ACT )\s*[IVXivx\d]', text)

    if len(parts) <= 1:
        # Strategy 2: split by double-newline groups
        parts = re.split(r'\n\s*\n\s*\n', text)

    # Group small parts together
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if len(current) + len(part) <= max_len:
            current = (current + "\n\n" + part).strip() if current else part
        else:
            if len(current) >= min_len:
                chunks.append(current)
            current = part

    if len(current) >= min_len:
        chunks.append(current)

    # Handle chunks that are too long
    final = []
    for chunk in chunks:
        if min_len <= len(chunk) <= max_len:
            final.append(chunk)
        elif len(chunk) > max_len:
            # Split paragraph by paragraph
            paras = chunk.split('\n\n')
            sub_current = ""
            for para in paras:
                para = para.strip()
                if not para:
                    continue
                if len(sub_current) + len(para) + 2 <= max_len:
                    sub_current = (sub_current + "\n\n" + para).strip() if sub_current else para
                else:
                    if len(sub_current) >= min_len:
                        final.append(sub_current)
                    sub_current = para
            if len(sub_current) >= min_len:
                final.append(sub_current)

    return final

def write_doc(fout, seen_ids, author_slug, text, era, country, title, genre="play"):
    did = doc_id(author_slug, text)
    if did in seen_ids:
        return False
    seen_ids.add(did)
    record = {
        "register": "screenplay",
        "author": author_slug,
        "source_dataset": "dracor",
        "doc_id": did,
        "text": text,
        "metadata": {
            "era": str(era)[:20],
            "language": "en",
            "country": country,
            "genre": genre,
            "title": str(title)[:100],
        }
    }
    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0
    plays_fetched = 0

    with open(OUT, "w", encoding="utf-8") as fout:

        # 1. DraCor REST API - Shakespeare plays, maximally chunked
        print("Fetching DraCor shake corpus with fine chunking...", flush=True)
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

                    # Also try to get character-level texts for more chunks
                    text = get_play_text("shake", play_id)
                    if not text:
                        skipped += 1
                        continue

                    plays_fetched += 1
                    chunks = split_into_chunks(text)
                    play_count = 0
                    for chunk in chunks:
                        if write_doc(fout, seen_ids, author_slug, chunk, year, "UK", title):
                            count += 1; play_count += 1

                    time.sleep(0.15)

                print(f"  shake done: {count} chunks from {plays_fetched} plays", flush=True)
        except Exception as e:
            print(f"  shake failed: {e}", flush=True)

        # 2. Also try Greek/Roman corpora with English translations
        for corpus_name, lang_label, country in [("greek", "ancient_greek", "Greece"),
                                                   ("rom", "la", "Rome"),
                                                   ("cal", "es", "Spain")]:
            print(f"Trying {corpus_name} corpus...", flush=True)
            try:
                r = requests.get(f"{BASE}/corpora/{corpus_name}", timeout=30)
                if r.status_code != 200:
                    print(f"  {corpus_name}: HTTP {r.status_code}", flush=True)
                    continue
                plays = r.json().get("plays", [])
                print(f"  {corpus_name}: {len(plays)} plays", flush=True)

                corp_count = 0
                for play in plays[:30]:  # sample 30
                    play_id = play.get("name") or ""
                    title = play.get("title") or ""
                    authors = play.get("authors") or []
                    if not authors:
                        continue
                    author_name = authors[0].get("name") or "unknown"
                    if author_name.lower() in ("unknown", ""):
                        continue
                    author_slug = slug(author_name)
                    year = str(play.get("yearNormalized") or "")

                    text = get_play_text(corpus_name, play_id)
                    if not text:
                        continue

                    chunks = split_into_chunks(text)
                    for chunk in chunks:
                        if write_doc(fout, seen_ids, author_slug, chunk, year, country, title,
                                     genre="ancient_drama"):
                            count += 1; corp_count += 1

                    time.sleep(0.1)

                print(f"  {corpus_name}: +{corp_count} chunks", flush=True)
            except Exception as e:
                print(f"  {corpus_name} failed: {e}", flush=True)

        # 3. HuggingFace: alankent/ordinary_screenplays — scene-level dialogue
        print("Loading alankent/ordinary_screenplays...", flush=True)
        try:
            ds = load_dataset("alankent/ordinary_screenplays", split="train", streaming=True)
            ds_count = 0
            author_scene_counts = defaultdict(int)

            for row in ds:
                # Extract project as "author" (TV show)
                project = row.get("sceneProjectName") or row.get("episodeTitle") or ""
                if not project:
                    skipped += 1; continue

                author_slug = slug(project)

                # Build text from dialogue
                dialog = row.get("dialog") or []
                if isinstance(dialog, list):
                    parts = []
                    for d in dialog:
                        if isinstance(d, dict):
                            char = d.get("character", "")
                            line = d.get("line", "")
                            if char and line:
                                parts.append(f"{char}: {line}")
                    text = "\n".join(parts)
                elif isinstance(dialog, str):
                    text = dialog
                else:
                    skipped += 1; continue

                # Add directions
                directions = row.get("directions") or ""
                if directions and isinstance(directions, list):
                    directions = " ".join(str(d) for d in directions)
                location = row.get("locationName") or ""

                if location:
                    text = f"LOCATION: {location}\n\n{text}"

                text = text.strip()
                if not (200 <= len(text) <= 4000):
                    if len(text) > 4000:
                        text = text[:4000]
                        lp = text.rfind('\n')
                        if lp > 200:
                            text = text[:lp]
                        else:
                            skipped += 1; continue
                    else:
                        skipped += 1; continue

                if author_scene_counts[author_slug] >= 200:
                    skipped += 1; continue

                ep = str(row.get("episodeTitle") or "")
                if write_doc(fout, seen_ids, author_slug, text, "", "US", ep, genre="tv_screenplay"):
                    count += 1; ds_count += 1
                    author_scene_counts[author_slug] += 1
                else:
                    skipped += 1

            print(f"  alankent/ordinary_screenplays: {ds_count} scene docs", flush=True)
        except Exception as e:
            print(f"  alankent/ordinary_screenplays failed: {e}", flush=True)

        # 4. Try gutenberg drama works from matthh/gutenberg-poetry-corpus
        # This corpus includes all Gutenberg works, filter by drama keywords
        print("Trying matthh/gutenberg-poetry-corpus for drama works...", flush=True)
        try:
            ds = load_dataset("matthh/gutenberg-poetry-corpus", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                title = str(row.get("title") or "").lower()
                # Filter to drama/play titles
                if not any(k in title for k in ["play", "drama", "comedy", "tragedy",
                                                  "hamlet", "othello", "king lear", "macbeth",
                                                  "tempest", "midsummer", "merchant", "romeo"]):
                    continue

                text = row.get("content") or ""
                author = row.get("author") or ""
                if not text or not author:
                    continue

                text = text.strip()
                if not (200 <= len(text) <= 4000):
                    if len(text) > 4000:
                        trunc = text[:4000]
                        lp = trunc.rfind('\n')
                        if lp > 200:
                            text = trunc[:lp]
                        else:
                            continue
                    else:
                        continue

                author_slug = slug(author)
                era = str(row.get("author_birth") or "")
                if write_doc(fout, seen_ids, author_slug, text, era, "", str(row.get("title") or "")[:100]):
                    count += 1; ds_count += 1

                if ds_count >= 500:
                    break

            print(f"  gutenberg drama: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  gutenberg drama failed: {e}", flush=True)

        # 5. imsdb movie scripts
        print("Loading aneeshas/imsdb-drama-movie-scripts...", flush=True)
        try:
            ds = load_dataset("aneeshas/imsdb-drama-movie-scripts", split="train", streaming=True)
            ds_count = 0
            for row in ds:
                text = row.get("Drama") or row.get("text") or ""
                if not text:
                    skipped += 1; continue

                # Extract author/title from first lines (format: "TITLE\n\nWritten by AUTHOR")
                lines = text.split('\n')
                title = lines[0].strip() if lines else "Unknown"
                author = "unknown_screenplay"
                for i, line in enumerate(lines[:20]):
                    if "written by" in line.lower() or "screenplay by" in line.lower():
                        # Next line might be author
                        if i+1 < len(lines) and lines[i+1].strip():
                            author = lines[i+1].strip()
                        else:
                            m = re.search(r'(?:written|screenplay) by\s+(.+)', line, re.I)
                            if m:
                                author = m.group(1).strip()
                        break

                if author in ("unknown_screenplay", "unknown", ""):
                    # Use script title as author proxy (unique film)
                    author = slug(title) if title else "unknown"

                # Split script into chunks
                chunks = split_into_chunks(text)
                for chunk in chunks:
                    author_slug = slug(author)
                    if write_doc(fout, seen_ids, author_slug, chunk, "", "US", title, genre="movie_script"):
                        count += 1; ds_count += 1

                if ds_count >= 2000:
                    break

            print(f"  imsdb-drama-movie-scripts: {ds_count} chunks", flush=True)
        except Exception as e:
            print(f"  imsdb-drama-movie-scripts failed: {e}", flush=True)

    print(f"DraCor/Screenplay total: {count} docs, {skipped} skipped, plays={plays_fetched} -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} plays_fetched={plays_fetched}\n")

if __name__ == "__main__":
    main()
