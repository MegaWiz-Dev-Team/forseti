"""API Test Agent — Sprint 02.

ADK-based agent for API E2E testing using Gemini.
Note: google.adk may not be installed yet; this provides a compatible
Agent-like class that mirrors ADK's interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from forseti.tools.http_tools import http_get, http_post, http_put
from forseti.tools.assert_tools import assert_status, assert_json_field
from forseti.tools.auth_tools import admin_login


# ── Minimal Tool wrapper (ADK-compatible) ──

@dataclass
class Tool:
    """Minimal tool descriptor matching ADK FunctionTool interface."""
    name: str
    func: Callable
    description: str = ""


def _save_result(name: str, status: str, details: str = "") -> dict:
    """Save a test result to shared state (placeholder)."""
    return {"name": name, "status": status, "details": details}


# ── Agent class (ADK-compatible) ──

@dataclass
class ApiTestAgentConfig:
    """Configuration matching ADK Agent interface."""
    name: str = "api_test_agent"
    model: str = "gemini-3.1-flash-lite-preview"
    description: str = "Test API endpoints via HTTP requests"
    instruction: str = ""
    tools: list[Tool] = field(default_factory=list)


def create_api_test_agent() -> ApiTestAgentConfig:
    """Create and configure the API Test Agent.

    Returns an agent config with 7 tools for API testing.
    When google-adk is available, this will return an actual ADK Agent.
    """
    tools = [
        Tool(name="http_get", func=http_get, description="Send HTTP GET request"),
        Tool(name="http_post", func=http_post, description="Send HTTP POST request"),
        Tool(name="http_put", func=http_put, description="Send HTTP PUT request"),
        Tool(name="assert_status", func=assert_status, description="Assert HTTP status"),
        Tool(name="assert_json_field", func=assert_json_field, description="Assert JSON field"),
        Tool(name="admin_login", func=admin_login, description="Login as admin"),
        Tool(name="save_result", func=_save_result, description="Save test result"),
    ]

    instruction = """You are an API testing agent for the Cloud Super Hero platform.
Your job is to execute E2E test scenarios by making HTTP API calls.

For each test scenario:
1. Call the API endpoint with the specified method and body
2. Assert the status code matches the expected value
3. Assert response JSON fields match expected values
4. Save the result (pass/fail) with details

Important rules:
- Always use dryRun: true for email operations (invitations, reminders, scores, certificates)
- Never modify production data — only test against dev server
- Admin endpoints require auth: use admin_login first to get a token
- Report both successes and failures with clear details

Target: cloud-super-hero-dev (GCP project)
Admin: paripol@megawiz.co
Student: paripol.toopiroh@gmail.com
Batch: DEV-BATCH-01
"""

    return ApiTestAgentConfig(
        name="api_test_agent",
        model="gemini-3.1-flash-lite-preview",
        description="Test API endpoints via HTTP requests on Cloud Super Hero dev",
        instruction=instruction,
        tools=tools,
    )
