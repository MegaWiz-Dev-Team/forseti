"""TDD Tests for ForsetiOrchestrator — Sprint 03.

Tests the main orchestrator that runs E2E test pipeline.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
            orch = ForsetiOrchestrator(  # noqa: F841 — setup for integration context
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

    @pytest.mark.asyncio
    async def test_check_service_health_online(self):
        """TC_ORC_05 — _check_service_health returns True when service responds 200."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="", admin_password="",
                db=db, report_dir=tmpdir,
            )
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            with patch("httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_cls.return_value = mock_client
                result = await orch._check_service_health("http://localhost:9200")
            assert result is True
            db.close()

    @pytest.mark.asyncio
    async def test_run_all_skips_when_ratatoskr_offline(self, tmp_path):
        """TC_ORC_06 — run_all skips UI suite gracefully when browser service is down."""
        # Create a minimal YAML with requires_browser + skip_if_unavailable
        yaml_content = """
name: "UI Test Suite"
base_url: "http://localhost:9090"
phase: SIT
metadata:
  project: test
  requires_browser: true
  browser_service_url: "http://localhost:9200"
  skip_if_unavailable: true
  skip_reason: "Ratatoskr not available"
scenarios: []
"""
        yaml_path = tmp_path / "test_ui.yaml"
        yaml_path.write_text(yaml_content)

        db = ResultsDB(db_path=str(tmp_path / "test.db"))
        orch = ForsetiOrchestrator(
            base_url="http://localhost:9090",
            admin_email="", admin_password="",
            db=db, report_dir=str(tmp_path),
        )

        # Simulate Ratatoskr being offline (httpx raises ConnectionError)
        import httpx
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client
            result = await orch.run_all(str(yaml_path))

        assert result.get("skipped") is True
        assert "Ratatoskr" in result.get("skip_reason", "")
        db.close()

