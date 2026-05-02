#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE_DIR = REPO / "text-ip-adapter/data/pairs_v5_7_poetry_pair_audited_min25"
OUT_DIR = REPO / "text-ip-adapter/data/pairs_v5_10_poetry_llm_style_medium_strong"
SHARD_DIR = ROOT / "shards"
DECISION_DIR = ROOT / "decisions"

DECISIONS = {"keep", "delete", "edit"}
STYLE = {"strong", "medium", "weak"}
CLEAN = {"clean", "minor_issues", "dirty"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_pair(shard_idx: int) -> tuple[list[dict], list[str]]:
    shard_path = SHARD_DIR / f"pairs_v5_7_train_style_shard_{shard_idx:02d}.jsonl"
    decision_path = DECISION_DIR / f"decisions_shard_{shard_idx:02d}.jsonl"
    errors: list[str] = []
    source = load_jsonl(shard_path)
    if not decision_path.exists():
        return [], [f"missing decision file {decision_path}"]
    decisions = load_jsonl(decision_path)
    if len(source) != len(decisions):
        errors.append(f"shard {shard_idx:02d}: row count mismatch source={len(source)} decisions={len(decisions)}")
    merged = []
    for i, src in enumerate(source):
        if i >= len(decisions):
            break
        dec = decisions[i]
        prefix = f"shard {shard_idx:02d} row {i} pair {src.get('pair_id')}"
        if dec.get("pair_id") != src.get("pair_id"):
            errors.append(f"{prefix}: pair_id mismatch got {dec.get('pair_id')}")
        if dec.get("decision") not in DECISIONS:
            errors.append(f"{prefix}: bad decision {dec.get('decision')}")
        if dec.get("style_strength") not in STYLE:
            errors.append(f"{prefix}: bad style_strength {dec.get('style_strength')}")
        if dec.get("cleanliness") not in CLEAN:
            errors.append(f"{prefix}: bad cleanliness {dec.get('cleanliness')}")
        if not isinstance(dec.get("reason"), str) or not dec.get("reason", "").strip():
            errors.append(f"{prefix}: missing reason")
        merged.append((src, dec))
    return merged, errors


def main() -> int:
    all_rows: list[dict] = []
    all_decisions: list[dict] = []
    errors: list[str] = []
    for shard_idx in range(10):
        merged, shard_errors = validate_pair(shard_idx)
        errors.extend(shard_errors)
        for src, dec in merged:
            row = dict(src)
            row["style_audit_v2"] = {
                "decision": dec["decision"],
                "style_strength": dec["style_strength"],
                "cleanliness": dec["cleanliness"],
                "reason": dec["reason"],
            }
            if dec["decision"] == "edit":
                if dec.get("ref_text"):
                    row["ref_text"] = dec["ref_text"]
                if dec.get("target_text"):
                    row["target_text"] = dec["target_text"]
            all_decisions.append({**dec, "author": src.get("author")})
            if (
                dec["decision"] in {"keep", "edit"}
                and dec["style_strength"] in {"medium", "strong"}
                and dec["cleanliness"] in {"clean", "minor_issues"}
            ):
                all_rows.append(row)

    if errors:
        (ROOT / "validation_errors.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
        print(json.dumps({"ok": False, "errors": errors[:50], "error_count": len(errors)}, indent=2))
        return 1

    author_counts = Counter(row["author"] for row in all_rows)
    final_train = [row for row in all_rows if author_counts[row["author"]] >= 20]
    dropped_low_author = {author: count for author, count in sorted(author_counts.items()) if count < 20}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "train.jsonl", final_train)
    for split in ["val", "test", "probes_balanced", "probes_balanced_n24"]:
        rows = load_jsonl(SOURCE_DIR / f"{split}.jsonl")
        write_jsonl(OUT_DIR / f"{split}.jsonl", rows)

    summary = {
        "source": str(SOURCE_DIR),
        "output": str(OUT_DIR),
        "decision_counts": dict(Counter(d["decision"] for d in all_decisions).most_common()),
        "style_counts": dict(Counter(d["style_strength"] for d in all_decisions).most_common()),
        "cleanliness_counts": dict(Counter(d["cleanliness"] for d in all_decisions).most_common()),
        "kept_before_min_author": len(all_rows),
        "final_train_rows": len(final_train),
        "final_train_authors": len(set(row["author"] for row in final_train)),
        "dropped_low_author_after_filter": dropped_low_author,
        "final_author_counts": dict(sorted(Counter(row["author"] for row in final_train).items())),
    }
    (ROOT / "merge_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "description": "v5.7 pair-audited split filtered by LLM style audit v2 for clean medium/strong distinctive writing style.",
        "source_pair_set": str(SOURCE_DIR),
        "style_audit": str(ROOT),
        "splits": {},
    }
    for split in ["train", "val", "test", "probes_balanced", "probes_balanced_n24"]:
        path = OUT_DIR / f"{split}.jsonl"
        rows = load_jsonl(path)
        manifest["splits"][split] = {
            "rows": len(rows),
            "authors": len(set(row.get("author") for row in rows if row.get("author"))),
            "sha256": sha256_file(path),
        }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"ok": True, **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
