"""LLM client for translating natural language test steps to browser actions."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from forseti.config import LLMConfig
from forseti.models import ActionPlan, BrowserAction

logger = logging.getLogger("forseti.agent.llm")

# ── System prompt for action generation ─────────────────────────────

SYSTEM_PROMPT = """\
You are Forseti, an E2E test automation agent. Your job is to translate natural language \
test instructions into precise browser actions.

Given a test step description (which may be in Thai or English), generate a JSON array of \
browser actions to execute.

**Available action types:**
- `navigate` — Go to a URL. Requires `value` (the URL or path).
- `click` — Click an element. Requires `selector` (CSS selector, text content, or aria label).
- `type` — Type text into an input. Requires `selector` and `value`.
- `select` — Select an option from a dropdown. Requires `selector` and `value`.
- `wait` — Wait for an element or condition. Requires `selector` or `value` (time in ms).
- `screenshot` — Take a screenshot. Optional `value` for filename.
- `assert_text` — Assert text is visible on page. Requires `value` (the text to find).
- `assert_element` — Assert element exists. Requires `selector`.
- `scroll` — Scroll the page. Optional `value` ("up", "down", or pixel amount).
- `hover` — Hover over an element. Requires `selector`.

**Rules:**
1. Output ONLY valid JSON — an array of action objects.
2. Each action has: `type`, `selector` (nullable), `value` (nullable), `description`.
3. Use intelligent CSS selectors: prefer `[data-testid]`, `[aria-label]`, `[placeholder]`, \
   `button:has-text("...")`, `input[name="..."]`, etc.
4. If the step mentions navigating to a page, use `navigate` first.
5. For Thai language steps, understand the intent and map it correctly.

**Context:**
- Base URL: {base_url}
- Current page context will be provided when available.

**Example:**
Step: "กรอก username ว่า admin"
Output:
```json
[
  {{"type": "type", "selector": "input[name='username'], input[placeholder*='user' i], #username",\
 "value": "admin", "description": "Type 'admin' into username field"}}
]
```

Step: "กดปุ่ม Login"
Output:
```json
[
  {{"type": "click", "selector": "button:has-text('Login'), button[type='submit'], \
input[type='submit']", "description": "Click the Login button"}}
]
```
"""

ASSERTION_PROMPT = """\
You are Forseti, an E2E test assertion agent. Given the current page content and an expected \
result description, determine if the expected result is met.

**Expected result:** {expected}

**Page content (text snapshot):**
{page_content}

**Instructions:**
1. Analyze the page content against the expected result.
2. Return a JSON object with:
   - `passed` (boolean): whether the expected result is met
   - `reason` (string): explanation of why it passed or failed
   - `evidence` (string): relevant text from the page that supports your judgment

Output ONLY valid JSON.
"""


# ── LLM Client Interface ───────────────────────────────────────────


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def generate_actions(self, step_description: str, base_url: str) -> ActionPlan:
        """Translate a natural language step into browser actions."""
        ...

    @abstractmethod
    async def check_assertion(self, expected: str, page_content: str) -> dict:
        """Check if expected result matches page content."""
        ...

    def _parse_actions_response(self, response_text: str, step_description: str) -> ActionPlan:
        """Parse LLM response into an ActionPlan."""
        # Clean response: extract JSON from possible markdown code blocks
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            actions_data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM response as JSON: {text[:200]}")
            # Fallback: create a generic click action
            actions_data = [
                {
                    "type": "screenshot",
                    "description": f"Screenshot for: {step_description}",
                }
            ]

        actions = [BrowserAction(**a) for a in actions_data]
        return ActionPlan(step_description=step_description, actions=actions)

    def _parse_assertion_response(self, response_text: str) -> dict:
        """Parse assertion check response."""
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse assertion response: {text[:200]}")
            return {"passed": False, "reason": "Failed to parse LLM assertion response", "evidence": ""}


# ── Gemini Client ───────────────────────────────────────────────────


class GeminiClient(BaseLLMClient):
    """LLM client using Google Gemini API."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai

            api_key = self.config.api_key
            if not api_key:
                import os
                api_key = os.getenv("GEMINI_API_KEY", "")

            self._client = genai.Client(api_key=api_key)
        return self._client

    async def generate_actions(self, step_description: str, base_url: str) -> ActionPlan:
        """Use Gemini to translate step to actions."""
        client = self._get_client()
        prompt = SYSTEM_PROMPT.format(base_url=base_url)

        response = client.models.generate_content(
            model=self.config.model,
            contents=f"Translate this test step to browser actions:\n\n{step_description}",
            config={
                "system_instruction": prompt,
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            },
        )

        return self._parse_actions_response(response.text, step_description)

    async def check_assertion(self, expected: str, page_content: str) -> dict:
        """Use Gemini to check if expected result matches page."""
        client = self._get_client()
        prompt = ASSERTION_PROMPT.format(expected=expected, page_content=page_content[:8000])

        response = client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config={
                "temperature": 0.0,
                "max_output_tokens": 1024,
            },
        )

        return self._parse_assertion_response(response.text)


# ── Self-Hosted (OpenAI-Compatible) Client ──────────────────────────


class SelfHostedClient(BaseLLMClient):
    """LLM client for self-hosted models with OpenAI-compatible API."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url or "http://localhost:11434/v1",
                headers={"Authorization": f"Bearer {self.config.api_key}"}
                if self.config.api_key
                else {},
                timeout=60.0,
            )
        return self._client

    async def generate_actions(self, step_description: str, base_url: str) -> ActionPlan:
        """Use self-hosted LLM to translate step to actions."""
        client = self._get_client()
        prompt = SYSTEM_PROMPT.format(base_url=base_url)

        response = await client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"Translate this test step to browser actions:\n\n{step_description}",
                    },
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return self._parse_actions_response(text, step_description)

    async def check_assertion(self, expected: str, page_content: str) -> dict:
        """Use self-hosted LLM to check assertion."""
        client = self._get_client()
        prompt = ASSERTION_PROMPT.format(expected=expected, page_content=page_content[:8000])

        response = await client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return self._parse_assertion_response(text)


# ── Factory ─────────────────────────────────────────────────────────


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """Create an LLM client based on configuration."""
    if config.provider == "gemini":
        return GeminiClient(config)
    elif config.provider in ("openai_compatible", "self_hosted", "ollama"):
        return SelfHostedClient(config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.provider}")
