#!/usr/bin/env python3
"""Audit and curate the v2 clean pair corpus.

Reads:
  - train.v2_clean.jsonl
  - val.v2_clean.jsonl
  - test.v2_clean.jsonl

Writes:
  - train.v2_curated.jsonl
  - val.v2_curated.jsonl
  - test.v2_curated.jsonl
  - v2_curated_manifest.json

The curation rules are the Phase 1 conjunction from
prompt-adapters/program/NEXT_BEST_BET_PLAN.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shlex
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

SPLITS = ("train", "val", "test")
INPUT_SUFFIX = ".v2_clean.jsonl"
OUTPUT_SUFFIX = ".v2_curated.jsonl"
MANIFEST_NAME = "v2_curated_manifest.json"

REGISTER_ORDER = ("poetry", "essay", "speech", "screenplay")

RULE_GENERATED_RE = re.compile(
    r"^(?:Write a poem about|Draft an essay exploring|Compose a speech addressing|Write a dramatic scene exploring)\b",
    re.IGNORECASE,
)
SUSPICIOUS_STOPWORD_RE = re.compile(
    r"\b(?:thou|while|about|also|must|over)\b",
    re.IGNORECASE,
)
MR_AUTHOR_RE = re.compile(r"^mr_[a-z0-9_]+$")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")
FENCED_CODE_RE = re.compile(r"```|~~~")
JS_CSS_HTML_API_RE = re.compile(
    r"\b(?:function|const|let|var|class|return|import|export|document\.|window\.|<html|</html>|<body|</body>|<div|</div>|<script|</script>|<style|</style>|api\b|endpoint\b|fetch\(|axios\b|javascript\b|css\b|html\b)\b",
    re.IGNORECASE,
)
LISTICLE_OR_SUPPORT_RE = re.compile(
    r"\b(?:step\s*\d+|how to|guidelines?|troubleshooting|faq|support|customer support|install|download|setup|pricing|features|terms of service|privacy policy)\b",
    re.IGNORECASE,
)
SCREENPLAY_SCENE_RE = re.compile(
    r"^(?:INT|EXT|I/E|INT/EXT|EST)\b|^(?:FADE IN|FADE OUT|CUT TO|DISSOLVE TO|SMASH CUT TO)\b",
    re.IGNORECASE,
)
SCREENPLAY_CHARACTER_RE = re.compile(r"^[A-Z][A-Z0-9 .,'\"()-]{1,40}$")
SCREENPLAY_DIALOGUE_HINT_RE = re.compile(
    r"\b(?:V.O\.|O.S\.|CONT'D|CONTINUED|VOICE OVER|OFF SCREEN|CLOSE ON|WIDE ON)\b",
    re.IGNORECASE,
)
SCREENPLAY_TRANSITION_RE = re.compile(r"^[A-Z][A-Z ]+ TO:$")
OCR_FLAG_RE = re.compile(r"ocr[^0-9]*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def flatten_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        out: list[Any] = []
        for item in value.values():
            out.extend(flatten_values(item))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(flatten_values(item))
        return out
    return [value]


def get_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key, "")
    return value if isinstance(value, str) else "" if value is None else str(value)


def stripped_len(text: str) -> int:
    return len(text.strip())


def percent(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(100.0 * numerator / denominator, 2)


def percentile(values: list[int], p: float) -> int | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 1:
        return ordered[-1]
    pos = (len(ordered) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    frac = pos - lo
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * frac)


def length_stats(rows: list[dict[str, Any]], key: str) -> dict[str, int | float | None]:
    lengths = [stripped_len(get_text(row, key)) for row in rows]
    if not lengths:
        return {"mean": None, "p10": None, "p50": None, "p90": None}
    return {
        "mean": round(mean(lengths), 2),
        "p10": percentile(lengths, 0.10),
        "p50": percentile(lengths, 0.50),
        "p90": percentile(lengths, 0.90),
    }


def collect_string_values(row: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        if key not in row:
            continue
        value = row[key]
        for leaf in flatten_values(value):
            if isinstance(leaf, str):
                values.append(leaf)
            elif leaf is not None:
                values.append(str(leaf))
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        for key in keys:
            if key not in metadata:
                continue
            value = metadata[key]
            for leaf in flatten_values(value):
                if isinstance(leaf, str):
                    values.append(leaf)
                elif leaf is not None:
                    values.append(str(leaf))
    return values


def extract_ocr_scores(row: dict[str, Any]) -> list[float]:
    scores: list[float] = []
    for key in list(row.keys()) + (list(row["metadata"].keys()) if isinstance(row.get("metadata"), dict) else []):
        if "ocr" not in key.lower():
            continue
        value = row.get(key) if key in row else row.get("metadata", {}).get(key)
        for leaf in flatten_values(value):
            if isinstance(leaf, (int, float)):
                scores.append(float(leaf))
            elif isinstance(leaf, str):
                try:
                    scores.append(float(leaf))
                except ValueError:
                    pass
    for flag in flatten_values(row.get("flags", [])):
        if not isinstance(flag, str):
            continue
        match = OCR_FLAG_RE.search(flag)
        if match:
            scores.append(float(match.group(1)))
    return scores


def has_rule_generated_instruction(row: dict[str, Any]) -> bool:
    return bool(RULE_GENERATED_RE.search(get_text(row, "instruction")))


def has_suspicious_stopword_instruction(row: dict[str, Any]) -> bool:
    return bool(SUSPICIOUS_STOPWORD_RE.search(get_text(row, "instruction")))


def has_medium_source(row: dict[str, Any]) -> bool:
    values = collect_string_values(
        row,
        (
            "source_dataset",
            "source",
            "source_marker",
            "dataset",
            "origin",
        ),
    )
    return any("medium" in value.lower() for value in values)


def has_un_debate_source(row: dict[str, Any]) -> bool:
    values = collect_string_values(
        row,
        (
            "source_dataset",
            "source",
            "source_marker",
            "dataset",
            "origin",
        ),
    )
    return any("un_debate" in value.lower() or "un debate" in value.lower() for value in values)


def is_mr_author(row: dict[str, Any]) -> bool:
    author = get_text(row, "author").strip().lower()
    return bool(MR_AUTHOR_RE.match(author))


def essay_has_non_literary_scaffolding(row: dict[str, Any]) -> bool:
    text = get_text(row, "target_text")
    return bool(
        URL_RE.search(text)
        or MARKDOWN_LINK_RE.search(text)
        or FENCED_CODE_RE.search(text)
        or JS_CSS_HTML_API_RE.search(text)
        or LISTICLE_OR_SUPPORT_RE.search(text)
    )


def screenplay_has_obvious_structure(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return False

    scene_hits = 0
    character_hits = 0
    dialogue_hits = 0
    transition_hits = 0

    for index, line in enumerate(lines):
        if SCREENPLAY_SCENE_RE.search(line):
            scene_hits += 1
        if SCREENPLAY_TRANSITION_RE.search(line):
            transition_hits += 1
        if SCREENPLAY_CHARACTER_RE.match(line) and len(line) <= 40 and line == line.upper():
            character_hits += 1
            if index + 1 < len(lines) and len(lines[index + 1].split()) > 1:
                dialogue_hits += 1
        if SCREENPLAY_DIALOGUE_HINT_RE.search(line):
            dialogue_hits += 1

    if scene_hits:
        return True
    if character_hits >= 2 and dialogue_hits >= 1:
        return True
    if transition_hits and dialogue_hits:
        return True
    if character_hits >= 3:
        return True
    return False


def mostly_whitespace(text: str) -> bool:
    raw_len = len(text)
    if raw_len == 0:
        return True
    non_ws = len(text.strip())
    return non_ws == 0 or (non_ws / raw_len) < 0.25


def register_value(row: dict[str, Any]) -> str:
    return get_text(row, "register").strip().lower() or "unknown"


def author_value(row: dict[str, Any]) -> str:
    return get_text(row, "author").strip() or "unknown"


def source_value(row: dict[str, Any]) -> str:
    values = collect_string_values(row, ("source_dataset", "source", "source_marker", "dataset", "origin"))
    return values[0].strip().lower() if values else ""


def row_passes_initial_filters(row: dict[str, Any]) -> tuple[bool, str | None]:
    target_text = get_text(row, "target_text")
    if stripped_len(target_text) < 100:
        return False, "target_len_lt_100"

    scores = extract_ocr_scores(row)
    if scores and max(scores) > 0.10:
        return False, "ocr_score_gt_0_10"

    if bool(row.get("short")):
        return False, "short_flag"

    reg = register_value(row)
    if reg == "speech" and is_mr_author(row) and has_un_debate_source(row):
        return False, "speech_mr_un_debate"

    if reg == "essay" and essay_has_non_literary_scaffolding(row):
        return False, "essay_non_literary_scaffolding"

    return True, None


def compute_split_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_register: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_register[register_value(row)].append(row)

    registers: dict[str, Any] = {}
    for reg in REGISTER_ORDER:
        subset = by_register.get(reg, [])
        if not subset:
            continue
        lengths_ref = length_stats(subset, "ref_text")
        lengths_target = length_stats(subset, "target_text")
        target_len_lt_100 = sum(1 for row in subset if stripped_len(get_text(row, "target_text")) < 100)
        scores = [max(extract_ocr_scores(row)) for row in subset if extract_ocr_scores(row)]
        rule_generated = sum(1 for row in subset if has_rule_generated_instruction(row))
        stopword_instr = sum(1 for row in subset if has_suspicious_stopword_instruction(row))

        reg_stats: dict[str, Any] = {
            "row_count": len(subset),
            "unique_authors": len({author_value(row) for row in subset}),
            "ref_text_length": lengths_ref,
            "target_text_length": lengths_target,
            "pct_target_len_below_100": percent(target_len_lt_100, len(subset)),
            "pct_rule_generated_instruction": percent(rule_generated, len(subset)),
            "pct_suspicious_stopword_instruction": percent(stopword_instr, len(subset)),
        }
        if scores:
            reg_stats["ocr_scored_rows"] = len(scores)
            reg_stats["pct_ocr_score_gt_0_10"] = percent(sum(1 for score in scores if score > 0.10), len(scores))
        else:
            reg_stats["ocr_scored_rows"] = 0
            reg_stats["pct_ocr_score_gt_0_10"] = None

        if reg == "essay":
            medium_source = sum(1 for row in subset if has_medium_source(row))
            scaffolding = sum(1 for row in subset if essay_has_non_literary_scaffolding(row))
            reg_stats["pct_medium_source"] = percent(medium_source, len(subset))
            reg_stats["pct_non_literary_web_scaffolding"] = percent(scaffolding, len(subset))
        elif reg == "speech":
            mr_authors = sum(1 for row in subset if is_mr_author(row))
            mr_un_debate = sum(1 for row in subset if is_mr_author(row) and has_un_debate_source(row))
            reg_stats["pct_mr_author_slug"] = percent(mr_authors, len(subset))
            reg_stats["pct_mr_author_and_un_debate"] = percent(mr_un_debate, len(subset))
        elif reg == "screenplay":
            whitespace = sum(1 for row in subset if mostly_whitespace(get_text(row, "target_text")))
            no_structure = sum(
                1 for row in subset if not screenplay_has_obvious_structure(get_text(row, "target_text"))
            )
            reg_stats["pct_target_mostly_whitespace"] = percent(whitespace, len(subset))
            reg_stats["pct_lacks_obvious_screenplay_structure"] = percent(no_structure, len(subset))

        registers[reg] = reg_stats

    return {
        "row_count": len(rows),
        "unique_authors": len({author_value(row) for row in rows}),
        "registers": registers,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_register: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_split[row.get("__split__", "")].append(row)
        by_register[register_value(row)].append(row)

    return {
        "overall": {
            "row_count": len(rows),
            "unique_authors": len({author_value(row) for row in rows}),
        },
        "by_split": {split: compute_split_audit(split_rows) for split, split_rows in by_split.items() if split},
        "by_register": {
            reg: {
                "row_count": len(reg_rows),
                "unique_authors": len({author_value(row) for row in reg_rows}),
            }
            for reg, reg_rows in by_register.items()
        },
    }


def count_by_split_and_register(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        split = row.get("__split__", "")
        reg = register_value(row)
        if split:
            counts[split][reg] += 1
    return {split: dict(regs) for split, regs in counts.items()}


def count_unique_authors_by_split_and_register(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    authors: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in rows:
        split = row.get("__split__", "")
        reg = register_value(row)
        if split:
            authors[split][reg].add(author_value(row))
    return {
        split: {reg: len(author_set) for reg, author_set in regs.items()}
        for split, regs in authors.items()
    }


def curation_pass(rows_by_split: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    removed_reason_counts: dict[str, int] = defaultdict(int)
    removed_by_split: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    filtered_by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    initial_screenplay_rows: list[dict[str, Any]] = []
    initial_screenplay_kept: list[dict[str, Any]] = []

    for split in SPLITS:
        for row in rows_by_split.get(split, []):
            row = dict(row)
            row["__split__"] = split
            passed, reason = row_passes_initial_filters(row)
            if register_value(row) == "screenplay":
                initial_screenplay_rows.append(row)
                if passed:
                    initial_screenplay_kept.append(row)
            if passed:
                filtered_by_split[split].append(row)
            else:
                if reason is None:
                    reason = "unknown"
                removed_reason_counts[reason] += 1
                removed_by_split[split][reason] += 1

    screenplay_ratio = (
        len(initial_screenplay_kept) / len(initial_screenplay_rows)
        if initial_screenplay_rows
        else 1.0
    )
    screenplay_dropped_entirely = screenplay_ratio < 0.30
    screenplay_removed_extra = 0

    if screenplay_dropped_entirely:
        for split in SPLITS:
            kept: list[dict[str, Any]] = []
            for row in filtered_by_split[split]:
                if register_value(row) == "screenplay":
                    screenplay_removed_extra += 1
                    removed_reason_counts["screenplay_register_dropped_below_30pct"] += 1
                    removed_by_split[split]["screenplay_register_dropped_below_30pct"] += 1
                    continue
                kept.append(row)
            filtered_by_split[split] = kept

    manifest = {
        "filter_rules": [
            "drop rows where stripped target_text length < 100",
            "drop rows with OCR score > 0.10 when OCR score exists",
            "drop rows carrying a short flag",
            "drop speech rows where author slug matches ^mr_ and source indicates un_debate",
            "drop essay rows matching the non-literary web/code/listicle regex set",
            "drop screenplay entirely if fewer than 30% of screenplay rows survive the above filters",
        ],
        "screenplay_retained_ratio_before_register_drop": round(screenplay_ratio, 4),
        "screenplay_dropped_entirely": screenplay_dropped_entirely,
        "screenplay_rows_removed_by_register_drop": screenplay_removed_extra,
        "removed_rows_by_reason": dict(sorted(removed_reason_counts.items())),
        "removed_rows_by_split": {
            split: dict(sorted(reasons.items())) for split, reasons in removed_by_split.items()
        },
    }
    return filtered_by_split, manifest


def build_count_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_split = defaultdict(list)
    by_register = defaultdict(list)
    for row in rows:
        by_split[row["__split__"]].append(row)
        by_register[register_value(row)].append(row)
    return {
        "by_split": {
            split: {
                "before": len(rows_for_split),
                "unique_authors_before": len({author_value(r) for r in rows_for_split}),
            }
            for split, rows_for_split in by_split.items()
        },
        "by_register": {
            reg: {
                "before": len(rows_for_reg),
                "unique_authors_before": len({author_value(r) for r in rows_for_reg}),
            }
            for reg, rows_for_reg in by_register.items()
        },
    }


def build_after_count_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_split = defaultdict(list)
    by_register = defaultdict(list)
    for row in rows:
        by_split[row["__split__"]].append(row)
        by_register[register_value(row)].append(row)
    return {
        "by_split": {
            split: {
                "after": len(rows_for_split),
                "unique_authors_after": len({author_value(r) for r in rows_for_split}),
            }
            for split, rows_for_split in by_split.items()
        },
        "by_register": {
            reg: {
                "after": len(rows_for_reg),
                "unique_authors_after": len({author_value(r) for r in rows_for_reg}),
            }
            for reg, rows_for_reg in by_register.items()
        },
    }


def merge_counts(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    out = {"by_split": {}, "by_register": {}}
    for split in SPLITS:
        before_split = before["by_split"].get(split, {})
        after_split = after["by_split"].get(split, {})
        out["by_split"][split] = {
            "before": before_split.get("before", 0),
            "after": after_split.get("after", 0),
            "unique_authors_before": before_split.get("unique_authors_before", 0),
            "unique_authors_after": after_split.get("unique_authors_after", 0),
        }
    for reg in REGISTER_ORDER:
        before_reg = before["by_register"].get(reg, {})
        after_reg = after["by_register"].get(reg, {})
        out["by_register"][reg] = {
            "before": before_reg.get("before", 0),
            "after": after_reg.get("after", 0),
            "unique_authors_before": before_reg.get("unique_authors_before", 0),
            "unique_authors_after": after_reg.get("unique_authors_after", 0),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and curate the v2 clean pair corpus.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "text-ip-adapter" / "data" / "pairs_v2",
        help="Directory containing train/val/test.v2_clean.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for curated jsonl and manifest. Defaults to input-dir.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = (args.output_dir or input_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    input_rows_by_split: dict[str, list[dict[str, Any]]] = {}
    input_files: dict[str, Path] = {}
    for split in SPLITS:
        path = input_dir / f"{split}{INPUT_SUFFIX}"
        if not path.exists():
            raise FileNotFoundError(f"Missing required input file: {path}")
        input_files[split] = path
        input_rows_by_split[split] = load_jsonl(path)

    all_input_rows: list[dict[str, Any]] = []
    for split in SPLITS:
        for row in input_rows_by_split[split]:
            row = dict(row)
            row["__split__"] = split
            all_input_rows.append(row)

    audit_before = {
        "overall": summarize_rows(all_input_rows)["overall"],
        "by_split": summarize_rows(all_input_rows)["by_split"],
    }

    filtered_by_split, curation_manifest = curation_pass(input_rows_by_split)
    curated_rows: list[dict[str, Any]] = []
    output_files: dict[str, Path] = {}
    for split in SPLITS:
        path = output_dir / f"{split}{OUTPUT_SUFFIX}"
        rows = []
        for row in filtered_by_split[split]:
            out = {k: v for k, v in row.items() if k != "__split__"}
            rows.append(out)
        write_jsonl(path, rows)
        output_files[split] = path
        curated_rows.extend({**row, "__split__": split} for row in rows)

    before_counts = build_count_table(all_input_rows)
    after_counts = build_after_count_table(curated_rows)
    counts = merge_counts(before_counts, after_counts)
    before_authors = {
        "overall": len({author_value(row) for row in all_input_rows}),
        "by_split": {
            split: len({author_value(row) for row in all_input_rows if row["__split__"] == split})
            for split in SPLITS
        },
    }
    before_authors["by_split"] = {
        split: len({author_value(row) for row in all_input_rows if row["__split__"] == split})
        for split in SPLITS
    }
    after_authors = {
        "overall": len({author_value(row) for row in curated_rows}),
        "by_split": {
            split: len({author_value(row) for row in curated_rows if row["__split__"] == split})
            for split in SPLITS
        },
    }

    total_input = len(all_input_rows)
    total_output = len(curated_rows)
    ag1 = total_output / total_input if total_input else 0.0

    manifest = {
        "corpus_version": "v2",
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "command": " ".join(shlex.quote(arg) for arg in sys.argv),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "input_files": {
            split: {"path": str(path), "sha256": sha256_file(path), "rows": len(input_rows_by_split[split])}
            for split, path in input_files.items()
        },
        "output_files": {
            split: {
                "path": str(path),
                "sha256": sha256_file(path),
                "rows": len(filtered_by_split[split]),
            }
            for split, path in output_files.items()
        },
        "audit": {
            "before": audit_before,
            "after": summarize_rows(curated_rows),
        },
        "counts": counts,
        "unique_authors": {
            "before": before_authors,
            "after": after_authors,
        },
        "removed_rows": curation_manifest,
        "gates": {
            "ag1_survival_fraction": round(ag1, 4),
            "ag1_pass": ag1 >= 0.60,
            "ag2_pass": all(
                sum(1 for row in curated_rows if register_value(row) == reg) >= 1500
                for reg in ("poetry", "essay", "speech")
            ),
            "ag3_pass": all(
                not (
                    {
                        author_value(row)
                        for row in curated_rows
                        if row["__split__"] == left
                    }
                    & {
                        author_value(row)
                        for row in curated_rows
                        if row["__split__"] == right
                    }
                )
                for left, right in (("train", "val"), ("train", "test"), ("val", "test"))
            ),
        },
    }

    manifest_path = output_dir / MANIFEST_NAME
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote curated splits to {output_dir}", flush=True)
    print(f"Wrote manifest to {manifest_path}", flush=True)
    print(json.dumps({"ag1_pass": manifest["gates"]["ag1_pass"], "ag2_pass": manifest["gates"]["ag2_pass"], "ag3_pass": manifest["gates"]["ag3_pass"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
