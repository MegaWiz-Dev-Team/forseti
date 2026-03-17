"""TDD Tests for Auth Tools — Sprint 02.

Red phase: Tests written before implementation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from forseti.tools.auth_tools import admin_login, get_auth_headers


class TestAdminLogin:
    """TC_SP02_11-12: admin_login authenticates with dev server."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """TC_SP02_11: Successful login returns token."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": "test-session-token"}

        with patch("forseti.tools.auth_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await admin_login(
                base_url="http://localhost:8080",
                email="admin@test.com",
                password="password123",
            )

        assert result["success"] is True
        assert result["token"] == "test-session-token"

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """TC_SP02_12: Wrong password returns error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "Invalid credentials"}

        with patch("forseti.tools.auth_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await admin_login(
                base_url="http://localhost:8080",
                email="admin@test.com",
                password="wrong",
            )

        assert result["success"] is False


class TestGetAuthHeaders:
    """TC_SP02_13: get_auth_headers builds Bearer header."""

    def test_returns_bearer_header(self):
        """TC_SP02_13: Token is wrapped in Bearer header."""
        headers = get_auth_headers(token="abc123")
        assert headers["Authorization"] == "Bearer abc123"
        assert headers["Content-Type"] == "application/json"
