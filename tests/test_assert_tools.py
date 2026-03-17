"""TDD Tests for Assert Tools — Sprint 02.

Red phase: Tests written before implementation.
"""
import pytest

from forseti.tools.assert_tools import assert_status, assert_json_field


class TestAssertStatus:
    """TC_SP02_06-07: assert_status checks HTTP status code."""

    def test_status_pass(self):
        """TC_SP02_06: Matching status returns passed=True."""
        result = assert_status(actual_status=200, expected_status=200)
        assert result["passed"] is True

    def test_status_fail(self):
        """TC_SP02_07: Non-matching status returns passed=False."""
        result = assert_status(actual_status=404, expected_status=200)
        assert result["passed"] is False
        assert "404" in result["message"]


class TestAssertJsonField:
    """TC_SP02_08-10: assert_json_field checks JSON response fields."""

    def test_field_pass(self):
        """TC_SP02_08: Existing field with matching value."""
        body = {"ok": True}
        result = assert_json_field(body=body, path="ok", expected=True)
        assert result["passed"] is True

    def test_field_nested(self):
        """TC_SP02_09: Nested field access with dot notation."""
        body = {"data": {"id": 1, "name": "test"}}
        result = assert_json_field(body=body, path="data.id", expected=1)
        assert result["passed"] is True
        assert result["actual"] == 1

    def test_field_missing(self):
        """TC_SP02_10: Missing field returns passed=False."""
        body = {}
        result = assert_json_field(body=body, path="name")
        assert result["passed"] is False
        assert "not found" in result["message"].lower()
