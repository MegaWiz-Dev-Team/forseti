"""HTTP Tools for API testing — Sprint 02.

Provides async HTTP methods for the ApiTestAgent.
"""
from __future__ import annotations

import httpx


async def http_get(url: str, headers: dict | None = None) -> dict:
    """Send GET request and return status + body.

    Args:
        url: Full URL to request.
        headers: Optional HTTP headers.

    Returns:
        {"status_code": int, "body": dict | str}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers or {})
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return {"status_code": resp.status_code, "body": body}


async def http_post(url: str, body: dict | None = None, headers: dict | None = None) -> dict:
    """Send POST request with JSON body.

    Args:
        url: Full URL to request.
        body: JSON body to send.
        headers: Optional HTTP headers.

    Returns:
        {"status_code": int, "body": dict | str}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body or {}, headers=headers or {})
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text
        return {"status_code": resp.status_code, "body": resp_body}


async def http_put(url: str, body: dict | None = None, headers: dict | None = None) -> dict:
    """Send PUT request with JSON body.

    Args:
        url: Full URL to request.
        body: JSON body to send.
        headers: Optional HTTP headers.

    Returns:
        {"status_code": int, "body": dict | str}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(url, json=body or {}, headers=headers or {})
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text
        return {"status_code": resp.status_code, "body": resp_body}
