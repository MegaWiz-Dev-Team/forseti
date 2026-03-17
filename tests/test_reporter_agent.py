"""TDD Tests for ReporterAgent — Sprint 03.

Tests the agent that generates reports and creates GitHub issues after test runs.
"""
import tempfile
from pathlib import Path
from datetime import datetime

from forseti.agents.reporter_agent import ReporterAgent
from forseti.models import (
    TestScript, TestScenario, TestStatus,
    TestSuiteResult, ScenarioResult, TestPhase,
)
from forseti.db.results_db import ResultsDB


def _make_result(passed: int = 4, failed: int = 1) -> TestSuiteResult:
    """Create a sample TestSuiteResult."""
    script = TestScript(
        name="CSH E2E", base_url="http://localhost:8080",
        phase=TestPhase.SIT, scenarios=[],
    )
    scenarios = []
    for i in range(passed):
        sc = TestScenario(name=f"TC_E2E_{i+1:02d}", steps=[], expected="OK")
        scenarios.append(ScenarioResult(scenario=sc, status=TestStatus.PASS, duration_ms=50))
    for i in range(failed):
        sc = TestScenario(name=f"TC_E2E_FAIL_{i+1}", steps=[], expected="OK")
        scenarios.append(ScenarioResult(
            scenario=sc, status=TestStatus.FAIL,
            error_message="Assertion failed", duration_ms=100,
        ))
    return TestSuiteResult(
        script=script, scenario_results=scenarios,
        started_at=datetime(2026, 3, 18), finished_at=datetime(2026, 3, 18, 0, 1),
    )


class TestReporterAgent:
    """Test ReporterAgent functionality."""

    def test_save_to_sqlite(self):
        """Results are saved to SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db)
            result = _make_result(passed=4, failed=1)

            run_id = agent.save_to_db(result)

            assert run_id > 0
            run = db.get_run(run_id)
            assert run["total"] == 5
            assert run["passed"] == 4
            assert run["failed"] == 1
            assert len(run["scenarios"]) == 5
            db.close()

    def test_generate_iso_report(self):
        """ISO SI-04 report is generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db, report_dir=tmpdir)
            result = _make_result()

            path = agent.generate_iso_report(result)

            assert Path(path).exists()
            content = Path(path).read_text()
            assert "SI-04" in content
            assert "80" in content  # 80% pass rate
            db.close()

    def test_generate_summary(self):
        """Human-readable summary is generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db)
            result = _make_result(passed=24, failed=2)

            summary = agent.generate_summary(result)

            assert "24" in summary
            assert "2" in summary
            assert "92" in summary  # ~92% pass rate
            db.close()

    def test_build_github_issue_body(self):
        """GitHub issue body contains failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db)
            result = _make_result(passed=4, failed=1)

            title, body = agent.build_github_issue(result)

            assert "Forseti" in title
            assert "TC_E2E_FAIL_1" in body
            assert "❌" in body
            assert "80" in body  # pass rate
            db.close()

    def test_no_issue_when_all_pass(self):
        """No GitHub issue when everything passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db)
            result = _make_result(passed=5, failed=0)

            issue = agent.build_github_issue(result)

            assert issue is None
            db.close()

    def test_full_report_pipeline(self):
        """Full pipeline: save DB + ISO report + summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            agent = ReporterAgent(db=db, report_dir=tmpdir)
            result = _make_result()

            report = agent.report(result)

            assert report["run_id"] > 0
            assert report["iso_report_path"] is not None
            assert report["summary"] is not None
            assert Path(report["iso_report_path"]).exists()
            db.close()
