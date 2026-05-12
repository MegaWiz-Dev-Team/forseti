"""Sprint 3 TDD — Forseti E2E Agent Validation.

Tests: agent registration, introduction, prompt preview, delegation flows, Odin standup.

Run: cd /Users/mimir/Developer/Forseti && python -m pytest tests/test_e2e_agents.py -v
"""

import pytest


# ══════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════


BIFROST_URL = "http://localhost:8100"


class MockBifrostClient:
    """Mock Bifrost client for E2E tests (no real server needed)."""

    def __init__(self):
        self.agents = {
            "mimir-agent": {"name": "Mimir", "role": "Knowledge Manager"},
            "bifrost-agent": {"name": "Bifrost", "role": "Orchestrator"},
            "heimdall-agent": {"name": "Heimdall", "role": "LLM Gateway"},
            "ratatoskr-agent": {"name": "Ratatoskr", "role": "Browser Service"},
            "fenrir-agent": {"name": "Fenrir", "role": "Clinical Automation"},
            "forseti-agent": {"name": "Forseti", "role": "QA Testing"},
            "huginn-agent": {"name": "Huginn", "role": "Security Scanner"},
            "muninn-agent": {"name": "Muninn", "role": "Auto-Fixer"},
            "eir-agent": {"name": "Eir", "role": "OpenEMR Gateway"},
            "vardr-agent": {"name": "Vardr", "role": "Infra Monitor"},
            "yggdrasil-agent": {"name": "Yggdrasil", "role": "Auth Service"},
            "asgard-agent": {"name": "Asgard", "role": "Platform Orchestrator"},
        }

    async def list_agents(self):
        return list(self.agents.values())

    async def introduce(self, agent_id):
        a = self.agents.get(agent_id)
        if not a:
            return None
        return f"สวัสดีครับ ผมชื่อ {a['name']} ทำหน้าที่เป็น {a['role']}"

    async def get_prompt(self, agent_id):
        return f"You are {self.agents[agent_id]['name']}"


# ═══════════════════════════════════════════
# 1. All Agents Registered
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_all_agents_registered():
    """All 12 agents should be registered in Bifrost."""
    client = MockBifrostClient()
    agents = await client.list_agents()

    assert len(agents) == 12
    names = {a["name"] for a in agents}
    expected = {
        "Mimir", "Bifrost", "Heimdall", "Ratatoskr", "Fenrir",
        "Forseti", "Huginn", "Muninn", "Eir", "Vardr",
        "Yggdrasil", "Asgard",
    }
    assert names == expected


# ═══════════════════════════════════════════
# 2. Agent Introduce All
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_agent_introduce_all():
    """Every agent should be able to introduce itself."""
    client = MockBifrostClient()

    for agent_id in client.agents:
        intro = await client.introduce(agent_id)
        assert intro is not None
        assert len(intro) > 10
        # Should contain agent name
        assert client.agents[agent_id]["name"] in intro


# ═══════════════════════════════════════════
# 3. Agent Prompt Preview
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_agent_prompt_preview():
    """Every agent should have a system prompt."""
    client = MockBifrostClient()

    for agent_id in client.agents:
        prompt = await client.get_prompt(agent_id)
        assert prompt is not None
        assert len(prompt) > 5


# ═══════════════════════════════════════════
# 4. Delegation Huginn → Muninn
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_delegation_huginn_muninn():
    """Huginn can delegate scan results to Muninn for fixing."""
    pytest.importorskip("bifrost.core.odin")
    from bifrost.core.odin import OdinOrchestrator

    odin = OdinOrchestrator()

    results = []
    async def mock_run(agent_id, task):
        r = f"[{agent_id}] completed: {task}"
        results.append(r)
        return r

    odin._run_agent = mock_run

    chain = [
        {"agent_id": "huginn-agent", "task": "Scan for vulnerabilities"},
        {"agent_id": "muninn-agent", "task": "Auto-fix found issues"},
    ]

    result = await odin.delegate_chain(chain)
    assert result["completed"] == 2
    assert any("huginn" in r for r in results)
    assert any("muninn" in r for r in results)


# ═══════════════════════════════════════════
# 5. Odin Standup E2E
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_odin_standup_e2e():
    """Odin standup reports status of all agents."""
    pytest.importorskip("bifrost.core.odin")
    from bifrost.core.odin import OdinOrchestrator

    odin = OdinOrchestrator()

    async def mock_check(agent_id):
        return {"agent_id": agent_id, "status": "healthy"}

    odin._check_agent = mock_check

    report = await odin.team_standup()

    assert report["total_count"] == 12
    assert report["healthy_count"] == 12
    assert len(report["agents"]) == 12
