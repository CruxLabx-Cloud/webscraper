"""Convert scrape results into export-ready formats (CSV / JSON)."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable


def to_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, indent=2, ensure_ascii=False)


def _flatten(d: dict[str, Any], prefix: str = "", sep: str = ".") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key, sep))
        elif isinstance(v, list):
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = v
    return out


def to_csv(items: Iterable[dict[str, Any]]) -> str:
    rows = [_flatten(it) for it in items]
    if not rows:
        return ""
    fieldnames: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    return buf.getvalue()
