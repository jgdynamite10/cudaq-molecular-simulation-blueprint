"""Write benchmark reports as JSON and CSV."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.benchmark.metrics import RunMetrics


def write_json_report(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def write_csv(path: Path, metrics: Sequence[RunMetrics]) -> Path:
    """Write per-run metrics as a flat CSV (one row per run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not metrics:
        path.write_text("")
        return path
    rows = [asdict(m) for m in metrics]
    fields = list(rows[0].keys())
    with path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            row["notes"] = json.dumps(row.get("notes", {}), default=str)
            writer.writerow(row)
    return path
