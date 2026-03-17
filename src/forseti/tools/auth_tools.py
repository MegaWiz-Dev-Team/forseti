"""Auth Tools for API testing — Sprint 02 + Sprint 04 (auth plugins).

Provides authentication for admin API access.
"""
from __future__ import annotations

import os

import httpx

from forseti.config import AuthConfig


async def admin_login(base_url: str, email: str, password: str) -> dict:
    """Login as admin and retrieve session token.

    Handles two flows:
    1. Direct token (if admin has otpVerified=True in Firestore)
    2. OTP dev mode (server returns dev_code → verify to get token)

    Returns:
        {"success": bool, "token": str | None, "error": str | None}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Login with password
        resp = await client.post(f"{base_url}/api/admin/login", json={
            "email": email,
            "password": password,
        })

        if resp.status_code == 200:
            data = resp.json()

            # Case A: Direct token (otpVerified user)
            if data.get("token"):
                return {"success": True, "token": data["token"]}

            # Case B: Dev mode OTP — server returned dev_code
            dev_code = data.get("dev_code")
            if dev_code:
                # Auto-verify OTP in dev mode
                verify_resp = await client.post(
                    f"{base_url}/api/admin/verify-otp",
                    json={"email": email, "code": dev_code},
                )
                if verify_resp.status_code == 200:
                    vdata = verify_resp.json()
                    token = vdata.get("token") or vdata.get("sessionToken", "")
                    if token:
                        return {"success": True, "token": token}

            return {"success": False, "token": None, "error": "No token in response"}
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


# ── Auth Plugin Factory (Sprint 04) ────────────────────────────────


def create_authenticator(auth_config: AuthConfig):
    """Create an async authenticator function based on auth config.

    Returns:
        An async function: (base_url: str) → {"success", "token", "headers"}
    """
    if auth_config.type == "none":
        async def _auth_none(base_url: str) -> dict:
            return {"success": True, "token": None, "headers": {}}
        return _auth_none

    elif auth_config.type == "otp":
        async def _auth_otp(base_url: str) -> dict:
            email = os.getenv(auth_config.email_env, "")
            password = os.getenv(auth_config.password_env, "")
            result = await admin_login(base_url, email, password)
            headers = get_auth_headers(result["token"]) if result.get("token") else {}
            return {**result, "headers": headers}
        return _auth_otp

    elif auth_config.type == "bearer":
        async def _auth_bearer(base_url: str) -> dict:
            token = os.getenv(auth_config.token_env, "")
            if not token:
                return {"success": False, "token": None, "headers": {},
                        "error": f"Missing env var: {auth_config.token_env}"}
            return {
                "success": True,
                "token": token,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        return _auth_bearer

    else:
        raise ValueError(f"Unknown auth type: {auth_config.type}")

