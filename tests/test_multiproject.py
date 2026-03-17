"""TDD Tests for Sprint 04 — Multi-Project Config + Auth Plugin.

Red phase: Tests written before implementation.
"""
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from forseti.config import ProjectConfig, AuthConfig, load_projects


class TestProjectConfig:
    """Tests for ProjectConfig model."""

    def test_load_project_config(self):
        """Parse forseti.yaml into ProjectConfig dict."""
        config_yaml = {
            "projects": {
                "cloud-super-hero": {
                    "base_url": "http://localhost:8080",
                    "test_script": "examples/test_scripts/cloud_super_hero_e2e.yaml",
                    "auth": {
                        "type": "otp",
                        "email_env": "TEST_ADMIN_EMAIL",
                        "password_env": "TEST_ADMIN_PASSWORD",
                        "login_path": "/api/admin/login",
                        "verify_path": "/api/admin/verify-otp",
                    },
                },
                "forseti-self": {
                    "base_url": "http://localhost:5555",
                    "test_script": "examples/test_scripts/forseti_self_test.yaml",
                    "auth": {"type": "none"},
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_yaml, f)
            f.flush()
            projects = load_projects(f.name)

        os.unlink(f.name)

        assert len(projects) == 2
        assert "cloud-super-hero" in projects
        assert "forseti-self" in projects

        csh = projects["cloud-super-hero"]
        assert isinstance(csh, ProjectConfig)
        assert csh.base_url == "http://localhost:8080"
        assert csh.auth.type == "otp"
        assert csh.auth.email_env == "TEST_ADMIN_EMAIL"

    def test_project_config_defaults(self):
        """ProjectConfig uses sensible defaults."""
        config_yaml = {
            "projects": {
                "simple": {
                    "base_url": "http://localhost:3000",
                    "test_script": "tests.yaml",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_yaml, f)
            f.flush()
            projects = load_projects(f.name)

        os.unlink(f.name)

        p = projects["simple"]
        assert p.auth.type == "none"  # default: no auth
        assert p.base_url == "http://localhost:3000"


class TestAuthPlugin:
    """Tests for auth plugin registry."""

    @pytest.mark.asyncio
    async def test_auth_none(self):
        """No-auth returns empty headers."""
        from forseti.tools.auth_tools import create_authenticator

        auth_config = AuthConfig(type="none")
        authenticator = create_authenticator(auth_config)
        result = await authenticator(base_url="http://localhost:5555")

        assert result["success"] is True
        assert result["token"] is None
        assert result["headers"] == {}

    @pytest.mark.asyncio
    async def test_auth_otp_mock(self):
        """OTP auth calls admin_login (mocked)."""
        from forseti.tools.auth_tools import create_authenticator

        auth_config = AuthConfig(
            type="otp",
            email_env="TEST_ADMIN_EMAIL",
            password_env="TEST_ADMIN_PASSWORD",
            login_path="/api/admin/login",
            verify_path="/api/admin/verify-otp",
        )

        with patch.dict(os.environ, {
            "TEST_ADMIN_EMAIL": "admin@test.com",
            "TEST_ADMIN_PASSWORD": "pass123",
        }):
            with patch("forseti.tools.auth_tools.admin_login", new_callable=AsyncMock) as mock_login:
                mock_login.return_value = {"success": True, "token": "mock-token"}
                authenticator = create_authenticator(auth_config)
                result = await authenticator(base_url="http://localhost:8080")

        assert result["success"] is True
        assert result["token"] == "mock-token"

    @pytest.mark.asyncio
    async def test_auth_bearer(self):
        """Bearer auth reads token from env var."""
        from forseti.tools.auth_tools import create_authenticator

        auth_config = AuthConfig(
            type="bearer",
            token_env="MY_API_TOKEN",
        )

        with patch.dict(os.environ, {"MY_API_TOKEN": "secret-bearer-token"}):
            authenticator = create_authenticator(auth_config)
            result = await authenticator(base_url="http://example.com")

        assert result["success"] is True
        assert result["token"] == "secret-bearer-token"
        assert result["headers"] == {"Authorization": "Bearer secret-bearer-token"}


class TestOrchestratorSuiteName:
    """Tests for orchestrator reading suite_name from YAML."""

    def test_suite_name_from_yaml(self):
        """Orchestrator reads suite_name from YAML metadata."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        yaml_content = {
            "suite_name": "My Custom Suite",
            "scenarios": [
                {"name": "TC_01", "method": "GET", "path": "/health", "expected_status": 200}
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = f"{tmpdir}/test.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(yaml_content, f)

            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator(
                base_url="http://localhost:8080",
                admin_email="a@b.com",
                admin_password="p",
                db=db,
                report_dir=tmpdir,
            )

            name = orch.get_suite_name(yaml_path)
            assert name == "My Custom Suite"
            db.close()

    def test_orchestrator_from_project_config(self):
        """Orchestrator can be created from ProjectConfig."""
        from forseti.agents.orchestrator import ForsetiOrchestrator
        from forseti.db.results_db import ResultsDB

        project = ProjectConfig(
            base_url="http://localhost:5555",
            test_script="examples/test_scripts/forseti_self_test.yaml",
            auth=AuthConfig(type="none"),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            orch = ForsetiOrchestrator.from_project(
                project=project,
                db=db,
                report_dir=tmpdir,
            )
            assert orch.base_url == "http://localhost:5555"
            db.close()
