"""TDD Tests for API Agent — Sprint 02.

Red phase: Tests written before implementation.
"""
import pytest

from forseti.agents.api_agent import create_api_test_agent


class TestApiTestAgent:
    """TC_SP02_14-16: ApiTestAgent configuration."""

    def test_agent_has_correct_tools(self):
        """TC_SP02_14: Agent has 7 tools registered."""
        agent = create_api_test_agent()
        tool_names = {t.name for t in agent.tools}
        expected = {"http_get", "http_post", "http_put", "assert_status",
                    "assert_json_field", "admin_login", "save_result"}
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"

    def test_agent_model_is_correct(self):
        """TC_SP02_15: Agent uses gemini-3.1-flash-lite-preview."""
        agent = create_api_test_agent()
        assert agent.model == "gemini-3.1-flash-lite-preview"

    def test_agent_instruction_is_set(self):
        """TC_SP02_16: Agent has non-empty instruction."""
        agent = create_api_test_agent()
        assert agent.instruction and len(agent.instruction) > 50
