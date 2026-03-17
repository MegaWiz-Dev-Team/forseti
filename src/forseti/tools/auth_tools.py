"""Auth Tools for API testing — Sprint 02.

Provides authentication for admin API access.
"""
from __future__ import annotations

import httpx


async def admin_login(base_url: str, email: str, password: str) -> dict:
    """Login as admin and retrieve session token.

    Returns:
        {"success": bool, "token": str | None, "error": str | None}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{base_url}/api/admin/login", json={
            "email": email,
            "password": password,
            "skipOtp": True,
        })

        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token") or data.get("sessionToken", "")
            return {"success": True, "token": token}
        else:
            return {"success": False, "token": None, "error": resp.text}


def get_auth_headers(token: str) -> dict:
    """Build authorization headers from token.

    Returns:
        {"Authorization": "Bearer <token>", "Content-Type": "application/json"}
    """
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
