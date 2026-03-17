"""TDD Tests for ISO Report Generator — Sprint 02.

Red phase: Tests written before implementation.
"""
import tempfile
from pathlib import Path
from datetime import datetime

from forseti.reporter.iso_report import ISOReportGenerator
from forseti.models import (
    TestScript, TestScenario, TestStatus,
    TestSuiteResult, ScenarioResult, TestPhase,
)


def _make_result(passed: int = 4, failed: int = 1) -> TestSuiteResult:
    """Create a sample TestSuiteResult for tests."""
    script = TestScript(
        name="Cloud Super Hero E2E",
        base_url="http://localhost:8080",
        phase=TestPhase.SIT,
        scenarios=[],
    )

    scenarios = []
    for i in range(passed):
        sc = TestScenario(name=f"Pass Scenario {i+1}", steps=[], expected="OK")
        sr = ScenarioResult(scenario=sc, status=TestStatus.PASS, duration_ms=100)
        scenarios.append(sr)

    for i in range(failed):
        sc = TestScenario(name=f"Fail Scenario {i+1}", steps=[], expected="OK")
        sr = ScenarioResult(
            scenario=sc, status=TestStatus.FAIL,
            error_message="Assertion failed", duration_ms=200,
        )
        scenarios.append(sr)

    return TestSuiteResult(
        script=script,
        scenario_results=scenarios,
        started_at=datetime(2026, 3, 18, 0, 0),
        finished_at=datetime(2026, 3, 18, 0, 1),
    )


class TestISOReportContent:
    """TC_SP02_17-20: ISO report content generation."""

    def test_generates_markdown(self):
        """TC_SP02_17: generate produces valid markdown string."""
        gen = ISOReportGenerator()
        result = _make_result()
        md = gen.generate(result)
        assert isinstance(md, str)
        assert len(md) > 100
        assert "# SI-04" in md

    def test_has_header_table(self):
        """TC_SP02_18: Report has correct SI-04 metadata header."""
        gen = ISOReportGenerator()
        result = _make_result()
        md = gen.generate(result)
        assert "SI-04" in md
        assert "Cloud Super Hero E2E" in md

    def test_has_test_matrix(self):
        """TC_SP02_19: Report has test matrix with correct row count."""
        gen = ISOReportGenerator()
        result = _make_result(passed=4, failed=1)
        md = gen.generate(result)
        # Should have 5 scenario rows
        assert md.count("✅") >= 4
        assert md.count("❌") >= 1

    def test_has_pass_rate(self):
        """TC_SP02_20: Report shows correct pass rate."""
        gen = ISOReportGenerator()
        result = _make_result(passed=4, failed=1)
        md = gen.generate(result)
        assert "80" in md  # 80% pass rate


class TestISOReportFile:
    """TC_SP02_21: ISO report file saving."""

    def test_saves_to_file(self):
        """TC_SP02_21: Report saves to markdown file on disk."""
        gen = ISOReportGenerator()
        result = _make_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.save(result, output_dir=tmpdir, filename="test_report.md")
            assert Path(path).exists()
            content = Path(path).read_text()
            assert "SI-04" in content
