#!/usr/bin/env python3
"""Download DraCor plays via pydracor API and canonicalize as screenplay/play register.
Targets English-language corpora (shake, greek, rom) + GerDraCor for diversity.
"""
import json, re, hashlib, sys, time
from pathlib import Path

RAW_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/raw/dracor")
OUT = Path("/workspace/text-ip-adapter/data/sources_v2/canonical/screenplay.jsonl")
LOG = RAW_DIR / "download.log"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def doc_id(author_slug, text):
    h = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"{author_slug}_{h}"

def get_play_text_via_api(corpus_name, play_name):
    """Fetch full play text using pydracor or REST API fallback."""
    import requests
    base = "https://dracor.org/api/v1"
    url = f"{base}/corpora/{corpus_name}/plays/{play_name}/spoken-text"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None

def split_play_into_docs(text, play_name, author_slug, min_len=200, max_len=4000):
    """Split a play into act-level or scene-level chunks."""
    # Try splitting by ACT
    acts = re.split(r'\n(?:ACT|Act|SCENE|Scene|AUFZUG|AKTE)\s+[IVXivx\d]+', text)
    docs = []
    for i, chunk in enumerate(acts):
        chunk = chunk.strip()
        if len(chunk) >= min_len:
            # Truncate if too long but keep a good chunk
            if len(chunk) > max_len:
                # Split further by scene within the act
                scenes = re.split(r'\n(?:SCENE|Scene|SZENE)\s+\d+', chunk)
                for j, sc in enumerate(scenes):
                    sc = sc.strip()
                    if min_len <= len(sc) <= max_len:
                        did = doc_id(author_slug, sc)
                        docs.append((did, sc))
                    elif len(sc) > max_len:
                        # Just truncate at max_len for a paragraph
                        trunc = sc[:max_len]
                        # Snap to last sentence
                        last_period = trunc.rfind('.')
                        if last_period > min_len:
                            trunc = trunc[:last_period+1]
                        did = doc_id(author_slug, trunc)
                        docs.append((did, trunc))
            else:
                did = doc_id(author_slug, chunk)
                docs.append((did, chunk))
    return docs

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("Fetching DraCor plays via REST API...", flush=True)

    import requests

    base = "https://dracor.org/api/v1"
    # Target corpora: english shakespeare, greek, roman, plus german for diversity
    target_corpora = ["shake", "greek", "rom", "ger", "cal", "u"]

    count = 0
    skipped = 0
    plays_fetched = 0
    seen_ids = set()

    with open(OUT, "w", encoding="utf-8") as fout:
        for corpus_name in target_corpora:
            print(f"  Fetching corpus: {corpus_name}", flush=True)
            try:
                r = requests.get(f"{base}/corpora/{corpus_name}", timeout=30)
                if r.status_code != 200:
                    print(f"  Corpus {corpus_name}: HTTP {r.status_code}, skipping", flush=True)
                    continue
                corpus_data = r.json()
                plays = corpus_data.get("plays", [])
                print(f"  {corpus_name}: {len(plays)} plays", flush=True)

                # Determine language
                lang_map = {
                    "shake": "en", "greek": "ancient_greek", "rom": "la",
                    "ger": "de", "cal": "es", "u": "de"
                }
                lang = lang_map.get(corpus_name, "en")
                # Only use English-language corpora for simplicity
                # But include ger since they wrote in German - use as-is
                if lang not in ("en",):
                    # Skip non-English for now to stay within scope
                    print(f"  Skipping non-English corpus {corpus_name} (lang={lang})", flush=True)
                    continue

                for play in plays[:100]:  # cap per corpus
                    play_id = play.get("name") or play.get("id") or ""
                    title = play.get("title") or play_id
                    authors = play.get("authors") or []
                    if not authors:
                        author_name = "unknown"
                    else:
                        author_name = authors[0].get("name") or authors[0].get("fullname") or "unknown"

                    if author_name.lower() in ("unknown", "anon", "anonymous", ""):
                        skipped += 1
                        continue

                    author_slug = slug(author_name)

                    # Get full spoken text
                    text = get_play_text_via_api(corpus_name, play_id)
                    if not text:
                        skipped += 1
                        continue

                    plays_fetched += 1
                    time.sleep(0.1)  # be gentle with API

                    # Split into docs
                    docs = split_play_into_docs(text, play_id, author_slug)
                    if not docs:
                        # Just use full text truncated
                        trunc = text[:4000]
                        if len(trunc) >= 200:
                            docs = [(doc_id(author_slug, trunc), trunc)]

                    year = str(play.get("yearNormalized") or play.get("writtenYear") or "")
                    country = "UK" if corpus_name == "shake" else (
                        "Greece" if corpus_name == "greek" else
                        "Rome" if corpus_name == "rom" else ""
                    )

                    for did, chunk in docs:
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
                                "language": lang,
                                "country": country,
                                "genre": "play",
                                "title": str(title)[:100],
                            }
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1

                    if count % 100 == 0:
                        print(f"  {count} docs from {plays_fetched} plays...", flush=True)

            except Exception as e:
                print(f"  Error in corpus {corpus_name}: {e}", flush=True)
                continue

    print(f"DraCor: {count} docs from {plays_fetched} plays, {skipped} skipped -> {OUT}", flush=True)
    with open(LOG, "w") as f:
        f.write(f"count={count} plays_fetched={plays_fetched} skipped={skipped}\n")

if __name__ == "__main__":
    main()
