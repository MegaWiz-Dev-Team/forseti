"""TDD Tests for ForsetiOrchestrator — Sprint 03.

Tests the main orchestrator that runs E2E test pipeline.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from forseti.agents.orchestrator import ForsetiOrchestrator
from forseti.db.results_db import ResultsDB


class TestForsetiOrchestrator:
    """Tests for the main ForsetiOrchestrator."""

    def test_create_orchestrator(self):
        """Orchestrator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="admin@test.com",
                admin_password="pass",
                db=db,
                report_dir=tmpdir,
            )
            assert orch.base_url == "http://localhost:8080"
            db.close()

    def test_build_api_scenarios(self):
        """Orchestrator builds API test scenarios from YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="admin@test.com",
                admin_password="pass",
                db=db,
                report_dir=tmpdir,
            )
            # Load real YAML
            yaml_path = str(Path(__file__).parent.parent / "examples" / "test_scripts" / "cloud_super_hero_e2e.yaml")
            scenarios = orch.load_yaml_scenarios(yaml_path)
            assert len(scenarios) >= 20
            db.close()

    @pytest.mark.asyncio
    async def test_run_single_scenario_mock(self):
        """Run a single mocked scenario returns result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="admin@test.com",
                admin_password="pass",
                db=db,
                report_dir=tmpdir,
            )

            # Mock the HTTP call
            mock_response = {"status_code": 200, "body": {"exists": True}}
            with patch("forseti.agents.orchestrator.http_post", new_callable=AsyncMock, return_value=mock_response):
                result = await orch.run_scenario({
                    "name": "TC_E2E_01",
                    "method": "POST",
                    "path": "/api/student/check-email",
                    "body": {"email": "test@test.com"},
                    "expected_status": 200,
                })

            assert result["status"] in ("pass", "fail")
            assert result["name"] == "TC_E2E_01"
            db.close()

    def test_report_generated_after_run(self):
        """After a run, reports are generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="admin@test.com",
                admin_password="pass",
                db=db,
                report_dir=tmpdir,
            )
            # Manually create a run to verify report generation
            from forseti.agents.reporter_agent import ReporterAgent
            from forseti.models import (
                TestScript, TestScenario, TestSuiteResult,
                ScenarioResult, TestStatus, TestPhase,
            )
            from datetime import datetime

            script = TestScript(name="test", base_url="http://localhost",
                              phase=TestPhase.SIT, scenarios=[])
            sc = TestScenario(name="TC_01", steps=[], expected="OK")
            suite = TestSuiteResult(
                script=script,
                scenario_results=[ScenarioResult(scenario=sc, status=TestStatus.PASS)],
                started_at=datetime.now(),
            )

            reporter = ReporterAgent(db=db, report_dir=tmpdir)
            report = reporter.report(suite)

            assert report["run_id"] > 0
            runs = db.get_runs()
            assert len(runs) == 1
            db.close()
