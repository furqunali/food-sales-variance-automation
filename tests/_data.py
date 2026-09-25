"""Shared test data: puts src/ + sample/ on the path, loads (or builds) the
deterministic sample dataset, and exposes per-(store, month) cells for
parametrized validation."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("src", "sample"):
    p = os.path.join(ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

SAMPLE_PATH = os.path.join(ROOT, "sample", "sample_data.json")
if not os.path.exists(SAMPLE_PATH):
    import generate_sample  # noqa: E402
    generate_sample.main()

SAMPLE = json.loads(open(SAMPLE_PATH, encoding="utf-8").read())
MONTHS = SAMPLE["months"]
DATA = SAMPLE["data"]

from generate_sample import STORES as _RAW_STORES  # noqa: E402
STORES = [{"id": s["id"], "name": s["name"]} for s in _RAW_STORES]

# Every (store_id, month_index) cell — used to parametrize data-integrity tests.
CELLS = [(sid, i) for sid in DATA for i in range(len(DATA[sid]))]
CELL_IDS = [f"{sid}-{DATA[sid][i]['m']}" for sid, i in CELLS]
STORE_IDS = list(DATA.keys())
