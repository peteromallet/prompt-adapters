#!/usr/bin/env python3
"""Download screenplay/drama content from multiple sources.
Robust chunking: split long texts into 200-4000 char chunks by sliding window over lines.
"""
import json, re, hashlib, sys, time, requests
from pathlib import Path
from collections import defaultdict
from datasets import load_dataset

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/dracor")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/screenplay.jsonl")
LOG = RAW_DIR / "download.log"

BASE = "https://dracor.org/api/v1"

MIN_LEN = 200
MAX_LEN = 4000

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

def robust_chunk(text, min_len=MIN_LEN, max_len=MAX_LEN):
    """
    Split text into chunks of min_len..max_len chars using a sliding line window.
    Guarantees all output chunks satisfy length bounds.
    """
    # Normalize line endings
    text = re.sub(r'\r\n?', '\n', text)
    lines = [l for l in text.split('\n') if l.strip()]

    chunks = []
    current_lines = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for \n

        if current_len + line_len > max_len and current_lines:
            # Flush current chunk
            chunk = '\n'.join(current_lines)
            if len(chunk) >= min_len:
                chunks.append(chunk)
            current_lines = []
            current_len = 0

        current_lines.append(line)
        current_len += line_len

    # Flush remainder
    if current_lines:
        chunk = '\n'.join(current_lines)
        if len(chunk) >= min_len:
            chunks.append(chunk)
        elif chunks:
            # Append to last chunk if it fits
            last = chunks[-1] + '\n' + chunk
            if len(last) <= max_len:
                chunks[-1] = last

    # Safety: truncate any that slipped through
    final = []
    for c in chunks:
        if len(c) > max_len:
            c = c[:max_len]
            lp = c.rfind('\n')
            if lp > min_len:
                c = c[:lp]
        if min_len <= len(c) <= max_len:
            final.append(c)

    return final

def write_doc(fout, seen_ids, author_slug, text, era, country, title, genre="play"):
    if not (MIN_LEN <= len(text) <= MAX_LEN):
        return False
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
            "country": str(country)[:50],
            "genre": genre,
            "title": str(title)[:100],
        }
    }
    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True

def ingest_corpus(fout, seen_ids, corpus_name, country, genre, max_plays=None):
    count = 0
    try:
        r = requests.get(f"{BASE}/corpora/{corpus_name}", timeout=30)
        if r.status_code != 200:
            print(f"  {corpus_name}: HTTP {r.status_code}", flush=True)
            return 0
        plays = r.json().get("plays", [])
        if max_plays:
            plays = plays[:max_plays]
        print(f"  {corpus_name}: {len(plays)} plays", flush=True)

        for play in plays:
            play_id = play.get("name") or ""
            title = play.get("title") or ""
            authors = play.get("authors") or []
            if not authors:
                continue
            author_name = authors[0].get("name") or "unknown"
            if author_name.lower() in ("unknown", ""):
                continue
            author_slug = slug(author_name)
            year = str(play.get("yearNormalized") or play.get("writtenYear") or "")

            text = get_play_text(corpus_name, play_id)
            if not text:
                continue

            chunks = robust_chunk(text)
            for chunk in chunks:
                if write_doc(fout, seen_ids, author_slug, chunk, year, country, title, genre):
                    count += 1

            time.sleep(0.1)

        print(f"  {corpus_name}: +{count} chunks", flush=True)
    except Exception as e:
        print(f"  {corpus_name} failed: {e}", flush=True)
    return count

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    count = 0
    skipped = 0

    with open(OUT, "w", encoding="utf-8") as fout:

        # 1. DraCor REST API corpora
        print("Fetching DraCor corpora...", flush=True)
        count += ingest_corpus(fout, seen_ids, "shake", "UK", "play")
        count += ingest_corpus(fout, seen_ids, "greek", "Greece", "ancient_drama", max_plays=40)
        count += ingest_corpus(fout, seen_ids, "rom", "Rome", "ancient_drama")
        count += ingest_corpus(fout, seen_ids, "u", "Austria", "play", max_plays=20)
        print(f"DraCor REST total so far: {count}", flush=True)

        # 2. HuggingFace: alankent/ordinary_screenplays
        print("Loading alankent/ordinary_screenplays...", flush=True)
        try:
            ds = load_dataset("alankent/ordinary_screenplays", split="train", streaming=True)
            ds_count = 0
            author_scene_counts = defaultdict(int)

            for row in ds:
                project = row.get("sceneProjectName") or row.get("episodeTitle") or "unknown"
                author_slug = slug(str(project))

                if author_scene_counts[author_slug] >= 200:
                    skipped += 1; continue

                # Build text
                dialog = row.get("dialog") or []
                parts = []
                if isinstance(dialog, list):
                    for d in dialog:
                        if isinstance(d, dict):
                            char = str(d.get("character") or "")
                            line = str(d.get("line") or "")
                            if line:
                                parts.append(f"{char}: {line}" if char else line)
                    text = "\n".join(parts)
                elif isinstance(dialog, str):
                    text = dialog
                else:
                    skipped += 1; continue

                loc = str(row.get("locationName") or "")
                if loc:
                    text = f"{loc}\n\n{text}"

                # May still be too short/long - use robust_chunk
                if len(text) < MIN_LEN:
                    skipped += 1; continue

                for chunk in (robust_chunk(text) if len(text) > MAX_LEN else [text.strip()]):
                    ep_title = str(row.get("episodeTitle") or "")
                    if write_doc(fout, seen_ids, author_slug, chunk, "", "US", ep_title, genre="tv_screenplay"):
                        count += 1; ds_count += 1
                        author_scene_counts[author_slug] += 1

            print(f"  alankent/ordinary_screenplays: {ds_count} docs", flush=True)
        except Exception as e:
            print(f"  alankent/ordinary_screenplays failed: {e}", flush=True)

        # 3. aneeshas/imsdb-drama-movie-scripts
        print("Loading aneeshas/imsdb-drama-movie-scripts...", flush=True)
        try:
            ds = load_dataset("aneeshas/imsdb-drama-movie-scripts", split="train", streaming=True)
            ds_count = 0
            script_authors = defaultdict(int)

            for row in ds:
                text = str(row.get("Drama") or row.get("text") or "")
                if not text:
                    skipped += 1; continue

                # Extract title (first non-empty line)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                title = lines[0] if lines else "Unknown"

                # Try to find author
                author = None
                for i, line in enumerate(lines[:30]):
                    m = re.search(r'(?:written|screenplay|script) by\s*[:\n]?\s*(.+)', line, re.I)
                    if m:
                        candidate = m.group(1).strip()
                        if candidate and len(candidate) < 60:
                            author = candidate
                            break

                if not author:
                    author = slug(title) or "unknown_script"

                author_slug = slug(str(author))
                if script_authors[author_slug] >= 100:
                    skipped += 1; continue

                chunks = robust_chunk(text)
                for chunk in chunks:
                    if write_doc(fout, seen_ids, author_slug, chunk, "", "US", title, genre="movie_script"):
                        count += 1; ds_count += 1
                        script_authors[author_slug] += 1

                if ds_count >= 3000:
                    break

            print(f"  imsdb: {ds_count} chunks", flush=True)
        except Exception as e:
            print(f"  imsdb failed: {e}", flush=True)

    # Final stats
    print(f"\nScreenplay total: {count} docs, {skipped} skipped -> {OUT}", flush=True)

    # Author stats
    author_counts = defaultdict(int)
    with open(OUT) as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    author_counts[r['author']] += 1
                except:
                    pass
    eligible = sum(1 for a, c in author_counts.items() if c >= 2)
    print(f"Authors: {len(author_counts)} total, {eligible} with >=2 docs", flush=True)

    with open(LOG, "w") as f:
        f.write(f"count={count} skipped={skipped} total_authors={len(author_counts)} eligible_authors={eligible}\n")

if __name__ == "__main__":
    main()
