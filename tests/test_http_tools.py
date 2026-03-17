"""TDD Tests for HTTP Tools — Sprint 02.

Red phase: Tests written before implementation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from forseti.tools.http_tools import http_get, http_post, http_put


class TestHttpGet:
    """TC_SP02_01: http_get returns status + body."""

    @pytest.mark.asyncio
    async def test_get_returns_status_and_body(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_resp.text = '{"status": "ok"}'

        with patch("forseti.tools.http_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await http_get(url="http://localhost:8080/health")

        assert result["status_code"] == 200
        assert result["body"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_with_auth_header(self):
        """TC_SP02_04: GET with Bearer auth."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"batchId": "DEV"}]
        mock_resp.text = "[]"

        with patch("forseti.tools.http_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await http_get(
                url="http://localhost:8080/api/admin/batches",
                headers={"Authorization": "Bearer test-token"},
            )

        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_get_no_auth_returns_401(self):
        """TC_SP02_05: GET without auth returns 401."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "Unauthorized"}
        mock_resp.text = '{"error": "Unauthorized"}'

        with patch("forseti.tools.http_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await http_get(url="http://localhost:8080/api/admin/batches")

        assert result["status_code"] == 401


class TestHttpPost:
    """TC_SP02_02: http_post sends JSON body."""

    @pytest.mark.asyncio
    async def test_post_sends_json(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"exists": True}
        mock_resp.text = '{"exists": true}'

        with patch("forseti.tools.http_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await http_post(
                url="http://localhost:8080/api/student/check-email",
                body={"email": "test@test.invalid"},
            )

        assert result["status_code"] == 200
        assert result["body"]["exists"] is True


class TestHttpPut:
    """TC_SP02_03: http_put sends update."""

    @pytest.mark.asyncio
    async def test_put_sends_update(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_resp.text = '{"ok": true}'

        with patch("forseti.tools.http_tools.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.put.return_value = mock_resp
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            result = await http_put(
                url="http://localhost:8080/api/programs/dev",
                body={"name": "Updated"},
            )

        assert result["status_code"] == 200
        assert result["body"]["ok"] is True
