"""FeedbackAgent — Sprint 06.

LLM-powered analysis of E2E/UI test results.
Provides expert feedback from two perspectives:
1. E2E Backend Expert — API quality, error handling, performance
2. UX/UI Expert — page structure, accessibility, user flow
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("forseti.agents.feedback")

# ── Prompts ──────────────────────────────────────────────────────────

BACKEND_EXPERT_PROMPT = """\
You are a Senior E2E Backend Testing Expert reviewing test results.
Analyze the following E2E test run results and provide actionable feedback.

**Test Run:**
- Suite: {suite_name}
- Pass Rate: {pass_rate}% ({passed}/{total})
- Duration: {duration_ms}ms
- Version: {version}

**Scenario Results:**
{scenario_details}

**Your task:**
Provide 3-5 specific, actionable suggestions to improve the backend quality.
Focus on:
- API response quality and error handling
- Missing test coverage areas
- Performance concerns (slow responses)
- Status code correctness
- Error message clarity

Return a JSON array of objects with:
- "category": one of "coverage", "performance", "error_handling", "security", "reliability"
- "severity": one of "high", "medium", "low"
- "suggestion": actionable recommendation (1-2 sentences)
- "scenario": which scenario this relates to (or "general")

Output ONLY valid JSON array.
"""

UI_EXPERT_PROMPT = """\
You are a Senior UX/UI Expert reviewing E2E test results for a web application.
Analyze the test scenarios and provide actionable UX/UI improvement suggestions.

**Test Run:**
- Suite: {suite_name}
- Base URL: {base_url}
- Scenarios tested: {total}
- Test types: {test_types}

**Scenario Results:**
{scenario_details}

**Your task:**
Provide 3-5 specific, actionable suggestions to improve UX/UI quality.
Focus on:
- User flow improvements
- Accessibility (a11y) gaps
- Error state handling in UI
- Loading/empty states
- Mobile responsiveness concerns
- Form validation feedback

Return a JSON array of objects with:
- "category": one of "accessibility", "user_flow", "error_states", "responsiveness", "performance", "forms"
- "severity": one of "high", "medium", "low"
- "suggestion": actionable recommendation (1-2 sentences)
- "scenario": which scenario this relates to (or "general")

Output ONLY valid JSON array.
"""


# ── FeedbackAgent ────────────────────────────────────────────────────


class FeedbackAgent:
    """Agent that analyzes test results using LLM and provides expert feedback.

    Uses Gemini (or compatible LLM) to analyze test run results from
    two perspectives: Backend Expert and UX/UI Expert.
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str = "",
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._client = None

    def _get_client(self):
        """Lazy-init Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _format_scenario_details(self, scenarios: list[dict]) -> str:
        """Format scenario results as readable text for LLM context."""
        lines = []
        for i, s in enumerate(scenarios, 1):
            icon = "✅" if s.get("status") == "pass" else "❌"
            name = s.get("name", "Unknown")
            duration = s.get("duration_ms", 0)
            error = s.get("error_message", "")
            sc_type = s.get("type", "api")
            line = f"{i}. {icon} [{sc_type.upper()}] {name} ({duration}ms)"
            if error:
                line += f"\n   Error: {error}"
            lines.append(line)
        return "\n".join(lines)

    def _detect_test_types(self, scenarios: list[dict]) -> str:
        """Detect what types of tests are in the run."""
        types = set()
        for s in scenarios:
            types.add(s.get("type", "api"))
        return ", ".join(sorted(types))

    def _call_llm(self, prompt: str) -> str:
        """Call LLM and return raw text response."""
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 2048,
            },
        )
        return response.text

    def _parse_feedback_json(self, text: str) -> list[dict]:
        """Parse LLM JSON response, with fallback."""
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            clean = "\n".join(lines)

        try:
            data = json.loads(clean)
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse feedback JSON: {clean[:200]}")
            return [{
                "category": "general",
                "severity": "low",
                "suggestion": "Unable to parse LLM feedback — check API key and model",
                "scenario": "general",
            }]

    def analyze(
        self,
        suite_name: str,
        base_url: str,
        pass_rate: float,
        passed: int,
        total: int,
        duration_ms: int,
        scenarios: list[dict],
        version: str = "unknown",
    ) -> dict:
        """Run full analysis from both expert perspectives.

        Returns:
            {
                "backend": [{"category", "severity", "suggestion", "scenario"}, ...],
                "ui": [{"category", "severity", "suggestion", "scenario"}, ...],
                "generated_at": "ISO timestamp"
            }
        """
        scenario_details = self._format_scenario_details(scenarios)
        test_types = self._detect_test_types(scenarios)

        # Backend Expert
        backend_prompt = BACKEND_EXPERT_PROMPT.format(
            suite_name=suite_name,
            pass_rate=pass_rate,
            passed=passed,
            total=total,
            duration_ms=duration_ms,
            version=version,
            scenario_details=scenario_details,
        )

        # UI Expert
        ui_prompt = UI_EXPERT_PROMPT.format(
            suite_name=suite_name,
            base_url=base_url,
            total=total,
            test_types=test_types,
            scenario_details=scenario_details,
        )

        try:
            logger.info("   🧠 Analyzing with Backend Expert...")
            backend_text = self._call_llm(backend_prompt)
            backend_feedback = self._parse_feedback_json(backend_text)
        except Exception as e:
            logger.warning(f"   ⚠️ Backend feedback failed: {e}")
            backend_feedback = [{
                "category": "general", "severity": "low",
                "suggestion": f"Feedback unavailable: {e}",
                "scenario": "general",
            }]

        try:
            logger.info("   🎨 Analyzing with UX/UI Expert...")
            ui_text = self._call_llm(ui_prompt)
            ui_feedback = self._parse_feedback_json(ui_text)
        except Exception as e:
            logger.warning(f"   ⚠️ UI feedback failed: {e}")
            ui_feedback = [{
                "category": "general", "severity": "low",
                "suggestion": f"Feedback unavailable: {e}",
                "scenario": "general",
            }]

        return {
            "backend": backend_feedback,
            "ui": ui_feedback,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_feedback_report(
        self,
        feedback: dict,
        suite_name: str,
        run_id: int,
        output_dir: str = "reports/feedback",
    ) -> str:
        """Generate markdown feedback report.

        Returns path to the generated report file.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = f"feedback_run{run_id}.md"
        filepath = Path(output_dir) / filename

        lines = [
            f"# 💡 Forseti Feedback — Run #{run_id}",
            f"**Suite:** {suite_name}",
            f"**Generated:** {feedback.get('generated_at', 'N/A')}",
            "",
            "---",
            "",
            "## 🔧 Backend Expert Feedback",
            "",
        ]

        for item in feedback.get("backend", []):
            sev = item.get("severity", "low")
            sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
            lines.append(
                f"- {sev_icon} **[{item.get('category', 'general')}]** "
                f"{item.get('suggestion', '')} "
                f"*({item.get('scenario', 'general')})*"
            )

        lines.extend([
            "",
            "## 🎨 UX/UI Expert Feedback",
            "",
        ])

        for item in feedback.get("ui", []):
            sev = item.get("severity", "low")
            sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
            lines.append(
                f"- {sev_icon} **[{item.get('category', 'general')}]** "
                f"{item.get('suggestion', '')} "
                f"*({item.get('scenario', 'general')})*"
            )

        lines.append(f"\n*Generated by Forseti ⚖️ at {feedback.get('generated_at', '')}*\n")

        filepath.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"   💡 Feedback report: {filepath}")
        return str(filepath)
