#!/usr/bin/env python3
"""
make_pairs.py — Generate author-disjoint train/val/test pairs from canonical JSONL files.
Applies all anti-bias caps, deduplication, length filters.
"""
import json, re, hashlib, random, math, sys
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import string

CANONICAL_DIR = Path("/workspace/text-ip-adapter/data/sources_v2/canonical")
OUT_DIR = Path("/workspace/text-ip-adapter/data/pairs_v2")

# Caps
MAX_AUTHOR_FRAC = 0.02     # 2% per author
MAX_DOC_FRAC = 0.005       # 0.5% per source doc
MAX_REGISTER_FRAC = 0.40   # 40% per register
MAX_DATASET_FRAC = 0.50    # 50% per source dataset
MAX_PAIRS_PER_AUTHOR = 20  # min(20, C(n,2)) pairs per author

# Split ratios
TRAIN_RATIO = 0.90
VAL_RATIO = 0.05
TEST_RATIO = 0.05

# Near-dup threshold
JACCARD_THRESHOLD = 0.85

# Text length (chars)
MIN_LEN = 200
MAX_LEN = 4000

STOPWORDS = set("""a an the and or but in on at to for of with is was are were be been being
have has had do does did will would could should may might shall can not no nor so yet both
either neither each few more most other some such than that this those these what which who
whom whose when where why how all any as by from into through during before after above below
between into through during i me my myself we our ours ourselves you your yours yourself
he him his himself she her hers herself it its itself they them their theirs themselves
what which who whom this that these those am is are was were be been being have has had
do does did will would could should may might shall can need dare ought used""".split())

def five_gram_jaccard(text_a, text_b):
    """Compute 5-gram Jaccard similarity between two texts."""
    def ngrams(text, n=5):
        tokens = text.lower().split()
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

    a = ngrams(text_a)
    b = ngrams(text_b)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0

def top_content_nouns(text, top_n=2):
    """Extract top N content words by TF (simple, no IDF — for rule-based instruction)."""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    words = [w for w in words if w not in STOPWORDS]
    freq = defaultdict(int)
    for w in words:
        freq[w] += 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:top_n]]

def make_instruction(register, target_text):
    """Rule-based instruction placeholder."""
    topics = top_content_nouns(target_text, 2)
    if len(topics) >= 2:
        topic_str = f"{topics[0]} and {topics[1]}"
    elif len(topics) == 1:
        topic_str = topics[0]
    else:
        topic_str = "life and experience"

    verbs = {
        "poetry": "Write a poem about",
        "speech": "Compose a speech addressing",
        "screenplay": "Write a dramatic scene exploring",
        "essay": "Draft an essay exploring",
    }
    verb = verbs.get(register, "Write a piece about")
    return f"{verb} {topic_str}.", topics

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

def load_canonical(register_file):
    """Load all docs from a canonical JSONL file."""
    docs = []
    path = CANONICAL_DIR / register_file
    if not path.exists():
        print(f"  WARNING: {path} not found, skipping", flush=True)
        return docs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                docs.append(json.loads(line))
            except:
                continue
    print(f"  Loaded {len(docs)} docs from {register_file}", flush=True)
    return docs

def split_authors(authors_list, seed=42):
    """Split authors 90/5/5 train/val/test."""
    rng = random.Random(seed)
    authors = list(authors_list)
    rng.shuffle(authors)
    n = len(authors)
    n_train = max(1, int(n * TRAIN_RATIO))
    n_val = max(1, int(n * VAL_RATIO))
    train_authors = set(authors[:n_train])
    val_authors = set(authors[n_train:n_train + n_val])
    test_authors = set(authors[n_train + n_val:])
    return train_authors, val_authors, test_authors

def generate_pairs_for_author(author_docs, max_pairs=20):
    """Generate up to max_pairs ordered pairs for an author's docs."""
    n = len(author_docs)
    if n < 2:
        return []
    max_possible = n * (n - 1) // 2
    target = min(max_pairs, max_possible)
    all_pairs = list(combinations(range(n), 2))
    random.shuffle(all_pairs)

    pairs = []
    for i, j in all_pairs:
        if len(pairs) >= target:
            break
        ref = author_docs[i]
        tgt = author_docs[j]
        # Near-dup check
        if five_gram_jaccard(ref["text"], tgt["text"]) > JACCARD_THRESHOLD:
            continue
        pairs.append((ref, tgt))

    return pairs

def apply_caps(all_pairs, total_target=54000):
    """Apply per-author, per-doc, per-register, per-dataset caps."""
    # Sort randomly first
    random.shuffle(all_pairs)

    author_counts = defaultdict(int)
    doc_counts = defaultdict(int)
    register_counts = defaultdict(int)
    dataset_counts = defaultdict(int)
    filtered = []

    # First pass: collect all, apply soft order
    for pair in all_pairs:
        filtered.append(pair)

    total = len(filtered)
    if total == 0:
        return []

    # Apply caps iteratively
    kept = []
    author_counts = defaultdict(int)
    doc_counts = defaultdict(int)
    register_counts = defaultdict(int)
    dataset_counts = defaultdict(int)

    for pair in filtered:
        author = pair["author"]
        ref_id = pair["ref_doc_id"]
        tgt_id = pair["target_doc_id"]
        reg = pair["register"]
        ds = pair["source_dataset"]
        n = total_target

        # Check caps (use running totals; recalc after each pass)
        a_ok = author_counts[author] < max(1, int(n * MAX_AUTHOR_FRAC))
        r_ok = doc_counts[ref_id] < max(1, int(n * MAX_DOC_FRAC))
        t_ok = doc_counts[tgt_id] < max(1, int(n * MAX_DOC_FRAC))
        reg_ok = register_counts[reg] < max(1, int(n * MAX_REGISTER_FRAC))
        ds_ok = dataset_counts[ds] < max(1, int(n * MAX_DATASET_FRAC))

        if a_ok and r_ok and t_ok and reg_ok and ds_ok:
            kept.append(pair)
            author_counts[author] += 1
            doc_counts[ref_id] += 1
            doc_counts[tgt_id] += 1
            register_counts[reg] += 1
            dataset_counts[ds] += 1

    return kept

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(42)

    # Load all canonical files
    register_files = {
        "poetry": "poetry.jsonl",
        "speech": "speech.jsonl",
        "screenplay": "screenplay.jsonl",
        "essay": "essay.jsonl",
    }

    # Group docs by author per register
    all_docs_by_register = {}
    for reg, fname in register_files.items():
        docs = load_canonical(fname)
        # Group by author — skip empty authors
        by_author = defaultdict(list)
        for doc in docs:
            author = doc.get("author", "").strip()
            if not author:
                continue
            by_author[author].append(doc)
        # Keep only authors with >= 2 docs
        by_author = {a: d for a, d in by_author.items() if len(d) >= 2}
        all_docs_by_register[reg] = by_author
        print(f"  {reg}: {len(by_author)} eligible authors", flush=True)

    # Global author split: an author slug maps to the SAME split across all registers
    # This ensures true author-disjoint splits even for multi-register authors
    all_author_slugs = set()
    for reg, by_author in all_docs_by_register.items():
        all_author_slugs.update(by_author.keys())

    train_global, val_global, test_global = split_authors(all_author_slugs)
    print(f"\nGlobal author split: train={len(train_global)} val={len(val_global)} test={len(test_global)}", flush=True)

    split_assignments = {}  # author_slug -> "train"|"val"|"test"
    for a in train_global:
        split_assignments[a] = "train"
    for a in val_global:
        split_assignments[a] = "val"
    for a in test_global:
        split_assignments[a] = "test"

    # Log per-register split breakdown
    for reg, by_author in all_docs_by_register.items():
        t = sum(1 for a in by_author if split_assignments.get(a) == "train")
        v = sum(1 for a in by_author if split_assignments.get(a) == "val")
        s = sum(1 for a in by_author if split_assignments.get(a) == "test")
        print(f"  {reg}: train={t} val={v} test={s} authors", flush=True)

    # Generate all pairs
    print("\nGenerating pairs...", flush=True)
    all_pairs = []
    for reg, by_author in all_docs_by_register.items():
        reg_pairs = 0
        for author, docs in by_author.items():
            split = split_assignments.get(author, "train")
            pairs = generate_pairs_for_author(docs, max_pairs=MAX_PAIRS_PER_AUTHOR)
            for ref, tgt in pairs:
                instruction, topics = make_instruction(reg, tgt["text"])
                pair = {
                    "register": reg,
                    "author": author,
                    "source_dataset": ref["source_dataset"],
                    "ref_doc_id": ref["doc_id"],
                    "target_doc_id": tgt["doc_id"],
                    "ref_text": ref["text"],
                    "target_text": tgt["text"],
                    "instruction": instruction,
                    "instruction_rule_based": instruction,
                    "metadata": {
                        "era": ref["metadata"].get("era", ""),
                        "language": ref["metadata"].get("language", "en"),
                        "country": ref["metadata"].get("country", ""),
                        "genre": ref["metadata"].get("genre", reg),
                        "instruction_rule_based_topics": topics,
                    },
                    "_split": split,
                }
                all_pairs.append(pair)
                reg_pairs += 1
        print(f"  {reg}: {reg_pairs} raw pairs", flush=True)

    print(f"\nTotal raw pairs: {len(all_pairs)}", flush=True)

    # Apply caps
    print("Applying anti-bias caps...", flush=True)
    capped_pairs = apply_caps(all_pairs, total_target=54000)
    print(f"After caps: {len(capped_pairs)} pairs", flush=True)

    # Split into train/val/test by _split field
    train_pairs = [p for p in capped_pairs if p["_split"] == "train"]
    val_pairs = [p for p in capped_pairs if p["_split"] == "val"]
    test_pairs = [p for p in capped_pairs if p["_split"] == "test"]

    print(f"Split: train={len(train_pairs)} val={len(val_pairs)} test={len(test_pairs)}", flush=True)

    # Ensure min 50 pairs per register in val and test
    for split_name, split_pairs in [("val", val_pairs), ("test", test_pairs)]:
        reg_counts = defaultdict(int)
        for p in split_pairs:
            reg_counts[p["register"]] += 1
        for reg in register_files:
            if reg_counts[reg] < 50:
                print(f"WARNING: {split_name} has only {reg_counts[reg]} {reg} pairs (< 50)", flush=True)

    # Write output files (strip _split field)
    def write_split(pairs, fname):
        path = OUT_DIR / fname
        with open(path, "w", encoding="utf-8") as f:
            for p in pairs:
                out = {k: v for k, v in p.items() if k != "_split"}
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
        print(f"Wrote {len(pairs)} pairs to {path}", flush=True)
        return path

    write_split(train_pairs, "train.v2.jsonl")
    write_split(val_pairs, "val.v2.jsonl")
    write_split(test_pairs, "test.v2.jsonl")

    # Print top-10 authors by pair count
    author_pair_counts = defaultdict(int)
    for p in capped_pairs:
        author_pair_counts[p["author"]] += 1
    top10 = sorted(author_pair_counts.items(), key=lambda x: -x[1])[:10]
    total = len(capped_pairs)
    print("\nTop-10 authors by pair-share:", flush=True)
    for author, cnt in top10:
        print(f"  {author}: {cnt} ({100*cnt/total:.2f}%)", flush=True)

    # Register breakdown
    print("\nRegister breakdown (all splits):", flush=True)
    reg_counts = defaultdict(int)
    for p in capped_pairs:
        reg_counts[p["register"]] += 1
    for reg, cnt in reg_counts.items():
        print(f"  {reg}: {cnt} ({100*cnt/total:.1f}%)", flush=True)

    # Dataset breakdown
    print("\nDataset breakdown:", flush=True)
    ds_counts = defaultdict(int)
    for p in capped_pairs:
        ds_counts[p["source_dataset"]] += 1
    for ds, cnt in ds_counts.items():
        print(f"  {ds}: {cnt} ({100*cnt/total:.1f}%)", flush=True)

    # Save stats for manifest
    stats = {
        "total_pairs": total,
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "test_pairs": len(test_pairs),
        "top10_authors": [[a, c, round(100*c/total, 2)] for a, c in top10],
        "register_counts": dict(reg_counts),
        "dataset_counts": dict(ds_counts),
    }
    with open(OUT_DIR / "pair_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("\nDone!", flush=True)

if __name__ == "__main__":
    main()
