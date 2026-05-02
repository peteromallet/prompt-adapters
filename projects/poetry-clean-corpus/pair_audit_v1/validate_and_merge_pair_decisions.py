#!/usr/bin/env python3
"""Validate pair-audit decisions and materialize a cleaned train split."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


VALID_DECISIONS = {"keep", "delete", "edit"}
VALID_SEVERITIES = {"none", "minor", "major"}
VALID_REASONS = {
    "ocr",
    "prose",
    "metadata",
    "style_mismatch",
    "weak_poem",
    "duplicate_like",
    "non_poetry",
    "prompt_junk",
    "foreign_language",
    "drama_or_dialogue",
    "other",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def validate_decision(row: dict, source_row: dict) -> list[str]:
    errors: list[str] = []
    if row.get("pair_id") != source_row.get("pair_id"):
        errors.append("pair_id_mismatch")
    if row.get("decision") not in VALID_DECISIONS:
        errors.append("invalid_decision")
    if row.get("severity") not in VALID_SEVERITIES:
        errors.append("invalid_severity")
    reasons = row.get("reasons")
    if not isinstance(reasons, list) or any(reason not in VALID_REASONS for reason in reasons):
        errors.append("invalid_reasons")
    if not isinstance(row.get("notes"), str):
        errors.append("invalid_notes")

    decision = row.get("decision")
    edited_ref = row.get("edited_ref_text")
    edited_target = row.get("edited_target_text")
    if decision == "keep":
        if row.get("severity") != "none":
            errors.append("keep_severity_not_none")
        if reasons:
            errors.append("keep_has_reasons")
        if edited_ref is not None or edited_target is not None:
            errors.append("keep_has_edits")
    elif decision == "delete":
        if row.get("severity") == "none":
            errors.append("delete_severity_none")
        if not reasons:
            errors.append("delete_missing_reasons")
        if edited_ref is not None or edited_target is not None:
            errors.append("delete_has_edits")
    elif decision == "edit":
        if row.get("severity") == "none":
            errors.append("edit_severity_none")
        if not reasons:
            errors.append("edit_missing_reasons")
        if edited_ref is None and edited_target is None:
            errors.append("edit_missing_text")
        for field_name, edited, original in (
            ("edited_ref_text", edited_ref, source_row.get("ref_text")),
            ("edited_target_text", edited_target, source_row.get("target_text")),
        ):
            if edited is None:
                continue
            if not isinstance(edited, str) or len(edited.strip()) < 40:
                errors.append(f"{field_name}_too_short")
            if isinstance(edited, str) and original and len(edited) < 0.55 * len(str(original)):
                errors.append(f"{field_name}_too_much_removed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-train", type=Path, required=True)
    parser.add_argument("--decisions-dir", type=Path, required=True)
    parser.add_argument("--output-train", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    source_rows = read_jsonl(args.source_train)
    by_pair_id = {row["pair_id"]: row for row in source_rows}
    decision_paths = sorted(args.decisions_dir.glob("decisions_shard_*.jsonl"))
    decisions: dict[str, dict] = {}
    errors: list[dict] = []

    for path in decision_paths:
        for line_index, decision in enumerate(read_jsonl(path), start=1):
            pair_id = decision.get("pair_id")
            if pair_id not in by_pair_id:
                errors.append({"path": str(path), "line": line_index, "pair_id": pair_id, "errors": ["unknown_pair_id"]})
                continue
            if pair_id in decisions:
                errors.append({"path": str(path), "line": line_index, "pair_id": pair_id, "errors": ["duplicate_decision"]})
                continue
            row_errors = validate_decision(decision, by_pair_id[pair_id])
            if row_errors:
                errors.append({"path": str(path), "line": line_index, "pair_id": pair_id, "errors": row_errors})
            decisions[pair_id] = decision

    missing = [row["pair_id"] for row in source_rows if row["pair_id"] not in decisions]
    if missing:
        errors.append({"errors": ["missing_decisions"], "count": len(missing), "examples": missing[:20]})

    kept: list[dict] = []
    decision_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()

    if not errors:
        for row in source_rows:
            decision = decisions[row["pair_id"]]
            decision_counts[decision["decision"]] += 1
            severity_counts[decision["severity"]] += 1
            reason_counts.update(decision.get("reasons", []))
            if decision["decision"] == "delete":
                continue
            out_row = dict(row)
            if decision["decision"] == "edit":
                if decision.get("edited_ref_text") is not None:
                    out_row["ref_text"] = decision["edited_ref_text"].strip()
                if decision.get("edited_target_text") is not None:
                    out_row["target_text"] = decision["edited_target_text"].strip()
                out_row["pair_audit_decision"] = "edit"
            else:
                out_row["pair_audit_decision"] = "keep"
            kept.append(out_row)
        write_jsonl(args.output_train, kept)

    summary = {
        "source_train": str(args.source_train),
        "decisions_dir": str(args.decisions_dir),
        "decision_files": [str(path) for path in decision_paths],
        "source_rows": len(source_rows),
        "decision_rows": len(decisions),
        "output_rows": len(kept) if not errors else None,
        "decision_counts": dict(decision_counts),
        "severity_counts": dict(severity_counts),
        "reason_counts": dict(reason_counts.most_common()),
        "errors": errors,
        "valid": not errors,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
