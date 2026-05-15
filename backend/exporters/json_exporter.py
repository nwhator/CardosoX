"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path


class JsonExporter:
    def dumps(self, results: list[dict]) -> str:
        return json.dumps(results, ensure_ascii=False, indent=2)

    def save(self, results: list[dict], path: str | Path) -> None:
        Path(path).write_text(self.dumps(results), encoding="utf-8")

