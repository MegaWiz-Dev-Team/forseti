"""TDD Tests for Sprint 05 — UI Testing + DB Verification.

Red phase: Tests written before implementation.
"""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml



# ─── 5A: UI Testing ──────────────────────────────────────────────────


class TestUIScenarioParsing:
    """Tests for UI scenario type in YAML parser."""

    def test_parse_ui_scenario(self):
        """UI scenario with type='ui' is parsed with steps."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            scenario = {
                "name": "Admin Login UI",
                "type": "ui",
                "steps": [
                    {"action": "navigate", "value": "/admin/login"},
                    {"action": "type", "selector": "#email", "value": "admin@test.com"},
                    {"action": "type", "selector": "#password", "value": "pass123"},
                    {"action": "click", "selector": "#loginBtn"},
                    {"action": "assert_text", "value": "Dashboard"},
                ],
                "tags": ["ui", "login"],
            }

            parsed = orch._parse_scenario(scenario)
            assert parsed is not None
            assert parsed["type"] == "ui"
            assert parsed["name"] == "Admin Login UI"
            assert len(parsed["steps"]) == 5
            assert parsed["steps"][0]["action"] == "navigate"
            db.close()

    def test_parse_api_scenario_default_type(self):
        """API scenarios default to type='api'."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            scenario = {
                "name": "Health Check",
                "method": "GET",
                "path": "/api/health",
                "expected_status": 200,
            }

            parsed = orch._parse_scenario(scenario)
            assert parsed["type"] == "api"
            db.close()


class TestUIScenarioExecution:
    """Tests for running UI scenarios through orchestrator."""

    @pytest.mark.asyncio
    async def test_run_ui_scenario(self):
        """UI scenario runs via BrowserEngine + ActionExecutor (mocked)."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            ui_scenario = {
                "name": "Login UI Flow",
                "type": "ui",
                "steps": [
                    {"action": "navigate", "value": "/login"},
                    {"action": "assert_text", "value": "Login"},
                ],
            }

            # Mock browser engine + page
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock()
            mock_page.get_by_text = MagicMock()
            mock_page.get_by_text.return_value.wait_for = AsyncMock()
            mock_page.screenshot = AsyncMock()
            mock_page.url = "http://localhost:8080"
            mock_page.set_default_timeout = MagicMock()

            with patch("forseti.browser.engine.BrowserEngine") as MockEngine:
                mock_engine_instance = AsyncMock()
                MockEngine.return_value = mock_engine_instance
                mock_engine_instance.start = AsyncMock()
                mock_engine_instance.stop = AsyncMock()

                # session context manager
                from contextlib import asynccontextmanager

                @asynccontextmanager
                async def mock_session(video_dir=None):
                    yield mock_page

                mock_engine_instance.session = mock_session

                orch.browser_service_url = "http://localhost:9200"
                result = await orch.run_scenario(ui_scenario)

            assert result["name"] == "Login UI Flow"
            assert result["status"] == "pass"
            db.close()


class TestUIYAMLScript:
    """Tests for loading UI scenarios from YAML."""

    def test_load_mixed_yaml(self):
        """YAML with both API and UI scenarios loads correctly."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        mixed_yaml = {
            "suite_name": "Mixed Suite",
            "scenarios": [
                {"name": "API health", "method": "GET", "path": "/health", "expected_status": 200},
                {
                    "name": "UI login",
                    "type": "ui",
                    "steps": [
                        {"action": "navigate", "value": "/login"},
                        {"action": "click", "selector": "#btn"},
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = f"{tmpdir}/mixed.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(mixed_yaml, f)

            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            scenarios = orch.load_yaml_scenarios(yaml_path)
            assert len(scenarios) == 2
            assert scenarios[0]["type"] == "api"
            assert scenarios[1]["type"] == "ui"
            db.close()


# ─── 5B: DB Verification ─────────────────────────────────────────────


class TestDBVerifyParsing:
    """Tests for db_verify field in YAML parser."""

    def test_parse_db_verify(self):
        """Scenario with db_verify field is parsed correctly."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            scenario = {
                "name": "Create then verify",
                "method": "POST",
                "path": "/api/data",
                "body": {"key": "value"},
                "expected_status": 200,
                "db_verify": {
                    "adapter": "sqlite",
                    "query": "SELECT * FROM items WHERE key='value'",
                    "expect_rows": 1,
                },
            }

            parsed = orch._parse_scenario(scenario)
            assert parsed["db_verify"] is not None
            assert parsed["db_verify"]["adapter"] == "sqlite"
            assert parsed["db_verify"]["expect_rows"] == 1
            db.close()

    def test_parse_no_db_verify(self):
        """Scenario without db_verify has None."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            scenario = {
                "name": "Simple GET",
                "method": "GET",
                "path": "/api/health",
                "expected_status": 200,
            }

            parsed = orch._parse_scenario(scenario)
            assert parsed.get("db_verify") is None
            db.close()


class TestDBAdapterRegistry:
    """Tests for DB adapter plugin registry."""

    def test_sqlite_adapter(self):
        """SQLite adapter queries and returns rows."""
        from forseti.tools.db_tools import create_db_adapter

        with tempfile.TemporaryDirectory() as tmpdir:
            import sqlite3
            db_path = f"{tmpdir}/test.db"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE items (key TEXT, value TEXT)")
            conn.execute("INSERT INTO items VALUES ('foo', 'bar')")
            conn.commit()
            conn.close()

            adapter = create_db_adapter("sqlite", {"db_path": db_path})
            rows = adapter.query("SELECT * FROM items WHERE key='foo'")
            assert len(rows) == 1
            assert rows[0]["key"] == "foo"

    def test_db_adapter_none(self):
        """No-op adapter for projects without DB verify."""
        from forseti.tools.db_tools import create_db_adapter

        adapter = create_db_adapter("none", {})
        rows = adapter.query("SELECT 1")
        assert rows == []

    def test_unknown_adapter_raises(self):
        """Unknown adapter type raises ValueError."""
        from forseti.tools.db_tools import create_db_adapter

        with pytest.raises(ValueError, match="Unknown db adapter"):
            create_db_adapter("mongodb", {})


# ─── 5C: Version Auto-Detection ──────────────────────────────────────


class TestVersionDetector:
    """Tests for version auto-detection from Git."""

    def test_detect_from_git_repo(self):
        """Detect version from a real git repository."""
        from forseti.tools.version_detector import detect_project_version

        # Use Forseti's own repo as test target
        result = detect_project_version(
            project_dir=str(Path(__file__).parent.parent)
        )
        assert result["commit"] != "unknown"
        assert len(result["commit"]) >= 7  # short SHA

    def test_detect_from_non_git_dir(self):
        """Non-git directory returns 'unknown'."""
        from forseti.tools.version_detector import detect_project_version

        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_project_version(project_dir=tmpdir)
            assert result["version"] == "unknown"
            assert result["commit"] == "unknown"

    def test_detect_none_dir(self):
        """None project_dir returns 'unknown'."""
        from forseti.tools.version_detector import detect_project_version

        result = detect_project_version(project_dir=None)
        assert result["version"] == "unknown"


class TestVersionInDB:
    """Tests for version tracking in ResultsDB."""

    def test_save_run_with_version(self):
        """Run record stores project_version and project_commit."""
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            run_id = db.save_run(
                suite_name="Test",
                phase="SIT",
                base_url="http://localhost",
                total=1, passed=1, failed=0, errors=0, skipped=0,
                duration_ms=100,
                project_version="v2.1.0",
                project_commit="c825675",
            )
            run = db.get_run(run_id)
            assert run["project_version"] == "v2.1.0"
            assert run["project_commit"] == "c825675"
            db.close()

    def test_save_run_without_version_defaults(self):
        """Run without version defaults to 'unknown'."""
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            run_id = db.save_run(
                suite_name="Test",
                phase="SIT",
                base_url="http://localhost",
                total=1, passed=1, failed=0, errors=0, skipped=0,
                duration_ms=100,
            )
            run = db.get_run(run_id)
            assert run["project_version"] == "unknown"
            assert run["project_commit"] == "unknown"
            db.close()


class TestProjectConfigWithDir:
    """Tests for project_dir in ProjectConfig."""

    def test_project_config_has_project_dir(self):
        """ProjectConfig includes optional project_dir field."""
        from forseti.config import ProjectConfig

        config = ProjectConfig(
            base_url="http://localhost:8080",
            test_script="test.yaml",
            project_dir="/path/to/project",
        )
        assert config.project_dir == "/path/to/project"

    def test_project_config_default_project_dir(self):
        """ProjectConfig defaults project_dir to empty string."""
        from forseti.config import ProjectConfig

        config = ProjectConfig(
            base_url="http://localhost:8080",
            test_script="test.yaml",
        )
        assert config.project_dir == ""
