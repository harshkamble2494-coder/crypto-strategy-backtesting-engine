from __future__ import annotations

import json
from pathlib import Path

from crypto_futures_bot.reporting.metrics import PerformanceMetrics


class ReportGenerator:
    def write_json(self, metrics: PerformanceMetrics, output_path: Path, metadata: dict[str, object] | None = None) -> None:
        payload: dict[str, object]
        if metadata:
            payload = {"metadata": metadata, "metrics": metrics.to_dict()}
        else:
            payload = metrics.to_dict()
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    def write_text(self, metrics: PerformanceMetrics, output_path: Path, metadata: dict[str, object] | None = None) -> None:
        lines: list[str] = []
        if metadata:
            lines.extend(f"{key}: {value}" for key, value in metadata.items())
            lines.append("")
        lines.extend(f"{key}: {value}" for key, value in metrics.to_dict().items())
        output_path.write_text("\n".join(lines), encoding="utf-8")
