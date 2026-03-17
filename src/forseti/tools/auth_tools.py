"""Auth Tools for API testing — Sprint 02.

Provides authentication for admin API access.
"""
from __future__ import annotations

import httpx


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
