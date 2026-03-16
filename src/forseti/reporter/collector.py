"""Result collection and aggregation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from forseti.models import TestSuiteResult

logger = logging.getLogger("forseti.reporter.collector")


class ResultCollector:
    """Collects and persists test results."""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, result: TestSuiteResult, filename: str | None = None) -> Path:
        """Save test suite result as JSON.

        Args:
            result: The test suite result to save.
            filename: Optional filename. Defaults to timestamped name.

        Returns:
            Path to the saved JSON file.
        """
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            phase = result.script.phase.value
            filename = f"forseti_{phase}_{ts}.json"

        path = self.results_dir / filename
        data = result.model_dump(mode="json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📄 Results saved: {path}")
        return path

    def load_json(self, path: str | Path) -> dict:
        """Load a previously saved result JSON."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_summary(self, result: TestSuiteResult) -> dict:
        """Generate a summary dict from test results."""
        return {
            "suite_name": result.script.name,
            "phase": result.script.phase.value,
            "base_url": result.script.base_url,
            "total_scenarios": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "skipped": result.skipped,
            "pass_rate": round(result.pass_rate, 1),
            "duration_ms": result.duration_ms,
            "started_at": str(result.started_at),
            "finished_at": str(result.finished_at),
        }
