"""ReporterAgent — Sprint 03.

Generates reports, saves to SQLite, and builds GitHub issue summaries.
Designed to run AFTER all tests complete (not during).
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from forseti.db.results_db import ResultsDB
from forseti.models import TestSuiteResult, TestStatus
from forseti.reporter.iso_report import ISOReportGenerator

logger = logging.getLogger("forseti.agents.reporter")


class ReporterAgent:
    """Agent that handles all reporting after a test run completes.

    Responsibilities:
    1. Save results to SQLite database
    2. Generate ISO SI-04 markdown report
    3. Generate human-readable summary
    4. Build GitHub issue body (only if failures exist)
    """

    def __init__(
        self,
        db: ResultsDB,
        report_dir: str = "reports",
    ):
        self.db = db
        self.report_dir = report_dir
        self.iso_gen = ISOReportGenerator()

    def report(self, result: TestSuiteResult, version_info: dict | None = None) -> dict:
        """Full report pipeline: DB + ISO + Summary.

        Returns:
            {"run_id": int, "iso_report_path": str, "summary": str,
             "github_issue": tuple | None, "version_info": dict}
        """
        vi = version_info or {"version": "unknown", "commit": "unknown"}
        run_id = self.save_to_db(result, version_info=vi)
        iso_path = self.generate_iso_report(result)
        summary = self.generate_summary(result)
        issue = self.build_github_issue(result)

        logger.info(f"📊 Report complete — Run #{run_id}")
        logger.info(f"   ISO: {iso_path}")
        logger.info(f"   {summary}")

        return {
            "run_id": run_id,
            "iso_report_path": str(iso_path),
            "summary": summary,
            "github_issue": issue,
            "version_info": vi,
        }

    def save_to_db(self, result: TestSuiteResult, version_info: dict | None = None) -> int:
        """Save test results to SQLite database."""
        vi = version_info or {"version": "unknown", "commit": "unknown"}
        run_id = self.db.save_run(
            suite_name=result.script.name,
            phase=result.script.phase.value,
            base_url=result.script.base_url,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            errors=result.errors,
            skipped=result.skipped,
            duration_ms=result.duration_ms,
            project_version=vi.get("version", "unknown"),
            project_commit=vi.get("commit", "unknown"),
        )

        for sr in result.scenario_results:
            self.db.save_scenario(
                run_id=run_id,
                name=sr.scenario.name,
                status=sr.status.value,
                duration_ms=sr.duration_ms,
                error_message=sr.error_message,
            )

        logger.info(f"💾 Saved to SQLite: Run #{run_id}")
        return run_id

    def generate_iso_report(self, result: TestSuiteResult) -> Path:
        """Generate ISO SI-04 markdown report."""
        return self.iso_gen.save(result, output_dir=self.report_dir)

    def generate_summary(self, result: TestSuiteResult) -> str:
        """Generate human-readable summary string."""
        return (
            f"⚖️ Forseti — {result.script.name}\n"
            f"   ✅ {result.passed}/{result.total} passed "
            f"({result.pass_rate:.0f}%) | "
            f"❌ {result.failed} failed | "
            f"⏱️ {result.duration_ms}ms"
        )

    def build_github_issue(self, result: TestSuiteResult) -> tuple[str, str] | None:
        """Build GitHub issue title + body for failures.

        Returns None if all tests passed (no issue needed).
        """
        if result.failed == 0 and result.errors == 0:
            return None

        title = (
            f"⚖️ [Forseti] E2E Results: "
            f"{result.passed}/{result.total} passed — "
            f"{result.script.name}"
        )

        lines = [
            "## ⚖️ Forseti E2E Test Results",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Suite | {result.script.name} |",
            f"| Phase | {result.script.phase.value} |",
            f"| URL | {result.script.base_url} |",
            f"| Pass Rate | **{result.pass_rate:.0f}%** |",
            f"| Total | {result.total} |",
            f"| ✅ Passed | {result.passed} |",
            f"| ❌ Failed | {result.failed} |",
            f"| ⚠️ Errors | {result.errors} |",
            "",
            "## Failed Scenarios",
            "",
        ]

        for sr in result.scenario_results:
            if sr.status in (TestStatus.FAIL, TestStatus.ERROR):
                icon = "❌" if sr.status == TestStatus.FAIL else "⚠️"
                lines.append(f"- {icon} **{sr.scenario.name}**: {sr.error_message or 'No details'}")

        lines.append("")
        lines.append(f"*Generated by Forseti ⚖️ at {datetime.now().isoformat()}*")

        return title, "\n".join(lines)
