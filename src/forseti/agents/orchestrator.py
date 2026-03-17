"""ForsetiOrchestrator — Sprint 03.

Main pipeline that runs API E2E tests and generates reports.
ADK-compatible design: runs scenarios sequentially, then reports.
"""
from __future__ import annotations

import asyncio
import logging
import time
import re
import json
from datetime import datetime
from pathlib import Path

import yaml

from forseti.agents.reporter_agent import ReporterAgent
from forseti.db.results_db import ResultsDB
from forseti.models import (
    TestScript, TestScenario, TestStep, TestPhase,
    TestSuiteResult, ScenarioResult, TestStatus,
)
from forseti.tools.http_tools import http_get, http_post, http_put
from forseti.tools.auth_tools import admin_login, get_auth_headers

logger = logging.getLogger("forseti.orchestrator")


class ForsetiOrchestrator:
    """Main orchestrator for running E2E API tests.

    Pipeline:
    1. Load YAML test script
    2. Authenticate (admin login)
    3. Run each scenario (API calls)
    4. Collect results
    5. Generate reports (ISO + SQLite)
    """

    def __init__(
        self,
        base_url: str,
        admin_email: str,
        admin_password: str,
        db: ResultsDB,
        report_dir: str = "reports",
    ):
        self.base_url = base_url
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.db = db
        self.reporter = ReporterAgent(db=db, report_dir=report_dir)
        self.admin_token: str | None = None

    def load_yaml_scenarios(self, yaml_path: str) -> list[dict]:
        """Load scenarios from YAML test script.

        Returns list of scenario dicts with parsed API details.
        """
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        scenarios = []
        for sc in data.get("scenarios", []):
            parsed = self._parse_scenario(sc)
            if parsed:
                scenarios.append(parsed)

        return scenarios

    def _parse_scenario(self, sc: dict) -> dict | None:
        """Parse a YAML scenario into executable format."""
        name = sc.get("name", "Unknown")
        steps = sc.get("steps", [])
        expected = sc.get("expected", "")
        tags = sc.get("tags", [])

        if not steps:
            return None

        action = steps[0].get("action", "") if steps else ""

        # Parse the NL action into method + path + body
        method, path, body = self._parse_action(action)

        # Determine expected status from expected string
        expected_status = 200
        status_match = re.search(r"Status (\d+)", expected)
        if status_match:
            expected_status = int(status_match.group(1))

        # Check if admin auth needed
        needs_auth = "admin auth" in action.lower() or "admin" in tags

        return {
            "name": name,
            "method": method,
            "path": path,
            "body": body,
            "expected_status": expected_status,
            "expected": expected,
            "needs_auth": needs_auth,
            "tags": tags,
        }

    def _parse_action(self, action: str) -> tuple[str, str, dict | None]:
        """Parse NL action string into (method, path, body)."""
        method = "GET"
        path = "/"
        body = None

        # Extract method
        action_upper = action.upper()
        if action_upper.startswith("POST"):
            method = "POST"
        elif action_upper.startswith("PUT"):
            method = "PUT"
        elif action_upper.startswith("GET"):
            method = "GET"

        # Extract path (first token starting with /)
        path_match = re.search(r"(/\S+)", action)
        if path_match:
            path = path_match.group(1)

        # Extract body from "with {..." or "and body {..."
        body_match = re.search(r"(?:with|body)\s+(\{.+\})\s*$", action)
        if body_match:
            try:
                # Attempt to parse as JSON-like (replace single quotes)
                body_str = body_match.group(1)
                body_str = body_str.replace("'", '"')
                # Handle unquoted keys by adding quotes
                body_str = re.sub(r'(\w+):', r'"\1":', body_str)
                body = json.loads(body_str)
            except (json.JSONDecodeError, ValueError):
                body = {}

        return method, path, body

    async def run_scenario(self, scenario: dict) -> dict:
        """Run a single API scenario.

        Returns:
            {"name": str, "status": "pass"|"fail"|"error",
             "duration_ms": int, "error": str | None}
        """
        name = scenario["name"]
        method = scenario["method"]
        path = scenario["path"]
        body = scenario.get("body")
        expected_status = scenario.get("expected_status", 200)
        needs_auth = scenario.get("needs_auth", False)

        start = time.monotonic()
        headers = {}

        try:
            if needs_auth and self.admin_token:
                headers = get_auth_headers(self.admin_token)

            url = f"{self.base_url}{path}"

            if method == "GET":
                resp = await http_get(url, headers=headers)
            elif method == "POST":
                resp = await http_post(url, body=body, headers=headers)
            elif method == "PUT":
                resp = await http_put(url, body=body, headers=headers)
            else:
                return {"name": name, "status": "error", "duration_ms": 0,
                        "error": f"Unknown method: {method}"}

            actual_status = resp["status_code"]
            duration_ms = int((time.monotonic() - start) * 1000)

            if actual_status == expected_status:
                return {"name": name, "status": "pass",
                        "duration_ms": duration_ms, "error": None}
            else:
                return {"name": name, "status": "fail",
                        "duration_ms": duration_ms,
                        "error": f"Expected {expected_status}, got {actual_status}"}

        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {"name": name, "status": "error",
                    "duration_ms": duration_ms, "error": str(e)}

    async def run_all(self, yaml_path: str) -> dict:
        """Run all scenarios from YAML and generate reports.

        Returns report dict from ReporterAgent.
        """
        logger.info("⚖️ Forseti — Starting E2E Test Run")

        # 1. Load scenarios
        scenarios = self.load_yaml_scenarios(yaml_path)
        logger.info(f"   Loaded {len(scenarios)} scenarios from YAML")

        # 2. Admin login
        logger.info(f"   Authenticating as {self.admin_email}...")
        auth_result = await admin_login(
            self.base_url, self.admin_email, self.admin_password
        )
        if auth_result["success"]:
            self.admin_token = auth_result["token"]
            logger.info("   ✅ Admin authenticated")
        else:
            logger.warning(f"   ⚠️ Admin auth failed: {auth_result.get('error')}")

        # 3. Run each scenario
        results = []
        for i, sc in enumerate(scenarios):
            logger.info(f"   [{i+1}/{len(scenarios)}] {sc['name']}...")
            result = await self.run_scenario(sc)
            results.append(result)

            icon = "✅" if result["status"] == "pass" else "❌"
            logger.info(f"   {icon} {result['status']} ({result['duration_ms']}ms)")

        # 4. Build TestSuiteResult for reporter
        suite_result = self._build_suite_result(scenarios, results, yaml_path)

        # 5. Generate reports
        report = self.reporter.report(suite_result)

        logger.info(f"\n{report['summary']}")
        return report

    def _build_suite_result(
        self,
        scenarios: list[dict],
        results: list[dict],
        yaml_path: str,
    ) -> TestSuiteResult:
        """Convert run results into TestSuiteResult for reporting."""
        script = TestScript(
            name="Cloud Super Hero E2E",
            base_url=self.base_url,
            phase=TestPhase.SIT,
            scenarios=[],
        )

        scenario_results = []
        for sc, res in zip(scenarios, results):
            test_scenario = TestScenario(
                name=sc["name"],
                steps=[],
                expected=sc.get("expected", ""),
                tags=sc.get("tags", []),
            )

            status_map = {
                "pass": TestStatus.PASS,
                "fail": TestStatus.FAIL,
                "error": TestStatus.ERROR,
            }

            scenario_results.append(ScenarioResult(
                scenario=test_scenario,
                status=status_map.get(res["status"], TestStatus.ERROR),
                duration_ms=res.get("duration_ms", 0),
                error_message=res.get("error"),
            ))

        return TestSuiteResult(
            script=script,
            scenario_results=scenario_results,
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
