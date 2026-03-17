"""Assert Tools for API testing — Sprint 02.

Provides assertion functions for validating API responses.
"""
from __future__ import annotations

from typing import Any


def assert_status(actual_status: int, expected_status: int) -> dict:
    """Assert HTTP status code matches expected.

    Returns:
        {"passed": bool, "message": str}
    """
    passed = actual_status == expected_status
    msg = (
        f"Status OK: {actual_status}" if passed
        else f"Expected {expected_status}, got {actual_status}"
    )
    return {"passed": passed, "message": msg}


def assert_json_field(
    body: dict,
    path: str,
    expected: Any = None,
) -> dict:
    """Assert a field exists (and optionally matches) in JSON body.

    Supports dot-notation for nested fields: "data.id"

    Returns:
        {"passed": bool, "message": str, "actual": Any}
    """
    parts = path.split(".")
    current = body

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return {
                "passed": False,
                "message": f"Field '{path}' not found in response",
                "actual": None,
            }
        current = current[part]

    # If no expected value, just check field exists
    if expected is None:
        return {
            "passed": True,
            "message": f"Field '{path}' exists",
            "actual": current,
        }

    passed = current == expected
    msg = (
        f"Field '{path}' = {current}" if passed
        else f"Field '{path}': expected {expected}, got {current}"
    )
    return {"passed": passed, "message": msg, "actual": current}
