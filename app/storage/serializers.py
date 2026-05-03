"""Helpers to serialize manifests and traces to JSON on disk."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_json(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    """Write ``payload`` to ``path`` as pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=False, default=_default)
        fp.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        result: dict[str, Any] = json.load(fp)
        return result
