"""Tests for Forseti result collector."""

import json
import pytest
from datetime import datetime
from pathlib import Path

from forseti.models import (
    ScenarioResult,
    TestPhase,
    TestScript,
    TestScenario,
    TestStatus,
    TestStep,
    TestSuiteResult,
)
from forseti.reporter.collector import ResultCollector


@pytest.fixture
def sample_result():
    """Create a sample TestSuiteResult for testing."""
    script = TestScript(
        name="Login Test",
        base_url="https://example.com",
        phase=TestPhase.SIT,
        scenarios=[],
    )
    result = TestSuiteResult(script=script)

    # Add pass scenario
    sc_pass = TestScenario(name="Login OK", steps=[TestStep(action="click")], expected="ok")
    result.scenario_results.append(
        ScenarioResult(scenario=sc_pass, status=TestStatus.PASS, duration_ms=500)
    )

    # Add fail scenario
    sc_fail = TestScenario(name="Login Fail", steps=[TestStep(action="click")], expected="error")
    result.scenario_results.append(
        ScenarioResult(
            scenario=sc_fail,
            status=TestStatus.FAIL,
            duration_ms=300,
            error_message="Assertion failed",
        )
    )

    result.finished_at = datetime.now()
    return result


class TestResultCollector:
    def test_save_and_load_json(self, tmp_path, sample_result):
        collector = ResultCollector(results_dir=str(tmp_path))
        path = collector.save_json(sample_result, filename="test_result.json")

        assert path.exists()
        data = collector.load_json(path)
        assert data["script"]["name"] == "Login Test"

    def test_get_summary(self, sample_result):
        collector = ResultCollector()
        summary = collector.get_summary(sample_result)

        assert summary["suite_name"] == "Login Test"
        assert summary["phase"] == "SIT"
        assert summary["total_scenarios"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["pass_rate"] == 50.0

    def test_auto_filename(self, tmp_path, sample_result):
        collector = ResultCollector(results_dir=str(tmp_path))
        path = collector.save_json(sample_result)

        assert path.exists()
        assert "forseti_SIT_" in path.name
