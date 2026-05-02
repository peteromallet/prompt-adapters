#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/../text-ip-adapter"

PYTHONPATH=src python - <<'PY'
from collections import Counter
from pathlib import Path

from text_ip_adapter.data.ingest_speeches import ingest_speeches
from text_ip_adapter.data.pairing import make_pairs, split_by_author

records = ingest_speeches(Path("data/raw/speeches"), max_speeches=1000, request_sleep=0)
print("records", len(records), "authors", len(Counter(r["author"] for r in records)))

for cap in (15, 30, 40, 50, 75):
    pairs = make_pairs(records, max_pairs_by_register={"speech": cap}, seed=42)
    splits = split_by_author(pairs, seed=42)
    print(
        "cap",
        cap,
        "total",
        len(pairs),
        "splits",
        {name: len(items) for name, items in splits.items()},
        "authors",
        {name: len({p["author"] for p in items}) for name, items in splits.items()},
    )
PY
