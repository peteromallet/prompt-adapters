#!/usr/bin/env python3
"""
audit.py — Validate anti-bias rules on final corpus.
Exits non-zero if any hard cap is violated.
"""
import json, sys, hashlib
from pathlib import Path
from collections import defaultdict

PAIRS_DIR = Path("/workspace/text-ip-adapter/data/pairs_v2")

CAPS = {
    "author_frac": 0.02,
    "doc_frac": 0.005,
    "register_frac": 0.40,
    "dataset_frac": 0.50,
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_all_pairs():
    pairs = []
    for fname in ["train.v2.jsonl", "val.v2.jsonl", "test.v2.jsonl"]:
        path = PAIRS_DIR / fname
        if not path.exists():
            print(f"WARNING: {path} not found")
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        pairs.append(json.loads(line))
                    except:
                        pass
    return pairs

def audit_split(pairs, split_name):
    """Audit a single split for cap violations."""
    total = len(pairs)
    if total == 0:
        return True, {}

    violations = []
    author_counts = defaultdict(int)
    doc_counts = defaultdict(int)
    register_counts = defaultdict(int)
    dataset_counts = defaultdict(int)
    register_authors = defaultdict(set)

    for p in pairs:
        author = p.get("author", "")
        ref_id = p.get("ref_doc_id", "")
        tgt_id = p.get("target_doc_id", "")
        reg = p.get("register", "")
        ds = p.get("source_dataset", "")

        author_counts[author] += 1
        doc_counts[ref_id] += 1
        doc_counts[tgt_id] += 1
        register_counts[reg] += 1
        dataset_counts[ds] += 1
        register_authors[reg].add(author)

    # Check author cap
    max_author = max(1, int(total * CAPS["author_frac"]))
    bad_authors = {a: c for a, c in author_counts.items() if c > max_author}
    if bad_authors:
        violations.append(f"Author cap violated: {len(bad_authors)} authors over {CAPS['author_frac']*100:.0f}% cap")
        for a, c in list(bad_authors.items())[:5]:
            violations.append(f"  {a}: {c}/{total} = {100*c/total:.2f}%")

    # Check doc cap
    max_doc = max(1, int(total * CAPS["doc_frac"]))
    bad_docs = {d: c for d, c in doc_counts.items() if c > max_doc}
    if bad_docs:
        violations.append(f"Doc cap violated: {len(bad_docs)} docs over {CAPS['doc_frac']*100:.1f}% cap")

    # Check register cap
    max_reg = max(1, int(total * CAPS["register_frac"]))
    for reg, cnt in register_counts.items():
        if cnt > max_reg:
            violations.append(f"Register cap violated: {reg} = {cnt}/{total} = {100*cnt/total:.1f}%")

    # Check dataset cap
    max_ds = max(1, int(total * CAPS["dataset_frac"]))
    for ds, cnt in dataset_counts.items():
        if cnt > max_ds:
            violations.append(f"Dataset cap violated: {ds} = {cnt}/{total} = {100*cnt/total:.1f}%")

    # Check author disjoint across splits (only meaningful when checking all splits)
    stats = {
        "total": total,
        "author_counts": dict(author_counts),
        "register_counts": dict(register_counts),
        "dataset_counts": dict(dataset_counts),
        "register_author_counts": {r: len(a) for r, a in register_authors.items()},
    }
    return len(violations) == 0, violations, stats

def main():
    print("=== AUDIT REPORT ===\n", flush=True)

    # SHA256 of output files
    file_stats = {}
    total_size = 0
    for fname in ["train.v2.jsonl", "val.v2.jsonl", "test.v2.jsonl"]:
        path = PAIRS_DIR / fname
        if path.exists():
            sha = sha256_file(path)
            size = path.stat().st_size
            total_size += size
            file_stats[fname] = {"sha256": sha, "size_bytes": size}
            print(f"{fname}: SHA256={sha} size={size/1024:.1f}KB", flush=True)
        else:
            print(f"{fname}: MISSING", flush=True)

    print()

    # Load all pairs
    all_pairs = load_all_pairs()
    print(f"Total pairs loaded: {len(all_pairs)}\n", flush=True)

    # Global audit (combined)
    ok, violations, stats = audit_split(all_pairs, "all")
    if violations:
        print("VIOLATIONS FOUND:")
        for v in violations:
            print(f"  {v}")
    else:
        print("All caps satisfied on combined corpus.")

    # Per-split breakdown
    splits = {}
    for fname in ["train.v2.jsonl", "val.v2.jsonl", "test.v2.jsonl"]:
        split_name = fname.split(".")[0]
        path = PAIRS_DIR / fname
        if path.exists():
            split_pairs = []
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            split_pairs.append(json.loads(line))
                        except:
                            pass
            s_ok, s_viol, s_stats = audit_split(split_pairs, split_name)
            splits[split_name] = s_stats
            print(f"\n{split_name}: {s_stats['total']} pairs")
            print(f"  Registers: {s_stats['register_counts']}")
            print(f"  Datasets: {s_stats['dataset_counts']}")
            if s_viol:
                for v in s_viol:
                    print(f"  VIOLATION: {v}")

    # Author disjoint check
    print("\n--- Author disjoint check ---", flush=True)
    split_authors = {}
    for fname in ["train.v2.jsonl", "val.v2.jsonl", "test.v2.jsonl"]:
        split_name = fname.split(".")[0]
        path = PAIRS_DIR / fname
        if path.exists():
            authors = set()
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            p = json.loads(line)
                            authors.add(p.get("author", ""))
                        except:
                            pass
            split_authors[split_name] = authors

    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        if a in split_authors and b in split_authors:
            overlap = split_authors[a] & split_authors[b]
            if overlap:
                print(f"WARNING: {a} ∩ {b} has {len(overlap)} shared authors! NOT DISJOINT!")
            else:
                print(f"  {a} ∩ {b} = empty (GOOD)")

    # Register balance in val/test
    print("\n--- Register balance val/test ---", flush=True)
    for split_name in ["val", "test"]:
        if split_name in splits:
            reg_counts = splits[split_name].get("register_counts", {})
            for reg, cnt in reg_counts.items():
                if cnt < 50:
                    print(f"WARNING: {split_name}/{reg} = {cnt} (< 50 minimum)")
                else:
                    print(f"  {split_name}/{reg} = {cnt} (ok)")

    # Write audit report
    report = {
        "file_stats": file_stats,
        "total_pairs": len(all_pairs),
        "splits": splits,
        "caps": CAPS,
        "violations": violations,
        "author_disjoint": {
            f"{a}_{b}": len(split_authors.get(a, set()) & split_authors.get(b, set())) == 0
            for a, b in [("train", "val"), ("train", "test"), ("val", "test")]
            if a in split_authors and b in split_authors
        }
    }
    with open(PAIRS_DIR / "audit_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nAudit report written to {PAIRS_DIR}/audit_report.json", flush=True)

    if violations:
        print("\nAudit FAILED with violations.", flush=True)
        sys.exit(1)
    else:
        print("\nAudit PASSED.", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
