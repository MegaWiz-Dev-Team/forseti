"""ForsetiOrchestrator — Sprint 03.

Main pipeline that runs API E2E tests and generates reports.
ADK-compatible design: runs scenarios sequentially, then reports.
"""
from __future__ import annotations

import logging
import os
import time
import re
import json
from datetime import datetime

import yaml

from forseti.agents.reporter_agent import ReporterAgent
from forseti.config import ProjectConfig
from forseti.config import BrowserConfig
from forseti.db.results_db import ResultsDB
from forseti.models import (
    TestScript, TestScenario, TestPhase,
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
        project_dir: str = "",
        github_repo: str = "",
        browser_service_url: str = "",
    ):
        self.base_url = base_url
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.db = db
        self.reporter = ReporterAgent(
            db=db,
            report_dir=report_dir,
            github_repo=github_repo,
        )
        self.admin_token: str | None = None
        self.report_dir = report_dir
        self.project_dir = project_dir
        self.github_repo = github_repo
        self.browser_service_url = browser_service_url or ""
        self.browser_base_url = ""  # Overridden from YAML browser_base_url metadata

    @classmethod
    def from_project(
        cls,
        project: ProjectConfig,
        db: ResultsDB,
        report_dir: str = "reports",
    ) -> ForsetiOrchestrator:
        """Create orchestrator from a ProjectConfig."""
        email = os.getenv(project.auth.email_env, "") if project.auth.email_env else ""
        password = os.getenv(project.auth.password_env, "") if project.auth.password_env else ""
        return cls(
            base_url=project.base_url,
            admin_email=email,
            admin_password=password,
            db=db,
            report_dir=report_dir,
            project_dir=project.project_dir,
            github_repo=project.github_repo,
        )

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

    def get_suite_name(self, yaml_path: str) -> str:
        """Read suite_name or name from YAML metadata."""
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("suite_name", data.get("name", "Unknown Suite"))

    def _parse_scenario(self, sc: dict) -> dict | None:
        """Parse a YAML scenario into executable format.

        Supports both structured format (method/path/body fields)
        and legacy NL format (steps[0].action string).
        """
        name = sc.get("name", "Unknown")
        tags = sc.get("tags", [])

        # Structured format (preferred)
        if "method" in sc and "path" in sc:
            return {
                "name": name,
                "type": sc.get("type", "api"),
                "method": sc["method"],
                "path": sc["path"],
                "body": sc.get("body"),
                "expected_status": sc.get("expected_status", 200),
                "expected": sc.get("expected", ""),
                "headers": sc.get("headers", {}),
                "needs_auth": sc.get("needs_auth", "admin" in tags),
                "tags": tags,
                "db_verify": sc.get("db_verify"),
            }

        # UI scenario format
        if sc.get("type") == "ui":
            return {
                "name": name,
                "type": "ui",
                "steps": sc.get("steps", []),
                "tags": tags,
            }

        # Legacy NL format (fallback)
        steps = sc.get("steps", [])
        expected = sc.get("expected", "")
        if not steps:
            return None

        action = steps[0].get("action", "") if steps else ""
        method, path, body = self._parse_action(action)

        expected_status = 200
        status_match = re.search(r"Status (\d+)", expected)
        if status_match:
            expected_status = int(status_match.group(1))

        needs_auth = "admin auth" in action.lower() or "admin" in tags

        return {
            "name": name,
            "type": "api",
            "method": method,
            "path": path,
            "body": body,
            "expected_status": expected_status,
            "expected": expected,
            "headers": sc.get("headers", {}),
            "needs_auth": needs_auth,
            "tags": tags,
            "db_verify": sc.get("db_verify"),
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
        """Run a single scenario (API or UI).

        Returns:
            {"name": str, "status": "pass"|"fail"|"error",
             "duration_ms": int, "error": str | None}
        """
        if scenario.get("type") == "ui":
            return await self._run_ui_scenario(scenario)
        return await self._run_api_scenario(scenario)

    async def _run_ui_scenario(self, scenario: dict) -> dict:
        """Run a UI scenario via BrowserEngine + ActionExecutor."""
        from pathlib import Path

        from forseti.browser.engine import BrowserEngine

        name = scenario["name"]
        steps = scenario.get("steps", [])
        start = time.monotonic()
        screenshot_path = None

        if not getattr(self, "browser_service_url", None):
            msg = "Skipped: No browser_service_url defined in test metadata (Ratatoskr required for UI tests)"
            import logging
            logging.getLogger("forseti.agents.orchestrator").warning(f"⏭️  {name} — {msg}")
            return {
                "name": name,
                "status": "skip",
                "duration_ms": int((time.monotonic() - start) * 1000),
                "error": msg,
            }

        try:
            config = BrowserConfig(headless=True)
            engine = BrowserEngine(config, ratatoskr_url=self.browser_service_url or None)
            await engine.start()

            async with engine.session() as page:
                for i, step_def in enumerate(steps):
                    action_type = step_def.get("action", "")
                    selector = step_def.get("selector")
                    value = step_def.get("value", "")

                    try:
                        # Resolve value for navigate
                        if action_type == "navigate":
                            # Use browser_base_url for Ratatoskr navigation (Docker service name)
                            # Falls back to base_url if not set
                            nav_base = getattr(self, "browser_base_url", "") or self.base_url
                            url = value if value.startswith("http") else f"{nav_base}{value}"
                            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        elif action_type == "click":
                            await page.locator(selector).click(timeout=30000)
                        elif action_type == "type":
                            await page.locator(selector).fill(value, timeout=30000)
                        elif action_type == "assert_text":
                            await page.get_by_text(value).wait_for(timeout=30000)
                        elif action_type == "assert_element":
                            await page.wait_for_selector(selector, timeout=30000)
                        elif action_type == "wait":
                            import asyncio as _asyncio
                            await _asyncio.sleep(int(value) / 1000 if value else 1)
                        elif action_type == "screenshot":
                            ss_dir = Path(self.report_dir) / "screenshots"
                            ss_dir.mkdir(parents=True, exist_ok=True)
                            ss_file = ss_dir / f"{name.replace(' ', '_')}__step{i + 1}.png"
                            await page.screenshot(path=str(ss_file))
                            screenshot_path = str(ss_file)

                    except Exception as step_err:
                        # Screenshot on failure
                        ss_dir = Path(self.report_dir) / "screenshots"
                        ss_dir.mkdir(parents=True, exist_ok=True)
                        safe_name = name.replace(" ", "_").replace("/", "_")
                        ss_file = ss_dir / f"{safe_name}__FAIL_step{i + 1}.png"
                        try:
                            await page.screenshot(path=str(ss_file))
                            screenshot_path = str(ss_file)
                        except Exception:
                            pass
                        raise step_err

            await engine.stop()

            duration_ms = int((time.monotonic() - start) * 1000)
            return {"name": name, "status": "pass",
                    "duration_ms": duration_ms, "error": None,
                    "screenshot": screenshot_path}

        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {"name": name, "status": "fail",
                    "duration_ms": duration_ms, "error": str(e),
                    "screenshot": screenshot_path}

    async def _run_api_scenario(self, scenario: dict) -> dict:
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
        custom_headers = scenario.get("headers", {})

        start = time.monotonic()
        headers = dict(custom_headers)

        try:
            if needs_auth and self.admin_token:
                headers.update(get_auth_headers(self.admin_token))

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

        # 0. Read top-level YAML metadata (for pre-flight checks)
        with open(yaml_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        yaml_meta = yaml_data.get("metadata", {})

        # 0.3 Update browser URLs from YAML metadata (overrides init value)
        if yaml_meta.get("browser_service_url"):
            self.browser_service_url = yaml_meta["browser_service_url"]
        if yaml_meta.get("browser_base_url"):
            self.browser_base_url = yaml_meta["browser_base_url"]

        # 0.5 Browser pre-flight check
        if yaml_meta.get("requires_browser") and yaml_meta.get("skip_if_unavailable"):
            browser_url = self.browser_service_url or yaml_meta.get("browser_service_url", "http://localhost:9200")
            browser_ok = await self._check_service_health(browser_url)
            if not browser_ok:
                skip_reason = yaml_meta.get(
                    "skip_reason",
                    f"Browser service unavailable at {browser_url}"
                )
                logger.warning(f"⚠️ Skipping UI test suite — {skip_reason}")
                return {
                    "summary": f"⏭️ SKIPPED — {skip_reason}",
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "skipped": True,
                    "skip_reason": skip_reason,
                }

        # 1. Load scenarios
        scenarios = self.load_yaml_scenarios(yaml_path)
        logger.info(f"   Loaded {len(scenarios)} scenarios from YAML")

        # 1.5 Detect project version
        from forseti.tools.version_detector import detect_project_version
        version_info = detect_project_version(project_dir=self.project_dir)
        logger.info(f"   📌 Version: {version_info['version']} ({version_info['commit']})")

        # 2. Admin login (non-fatal — UI tests don't need auth)
        logger.info(f"   Authenticating as {self.admin_email}...")
        try:
            auth_result = await admin_login(
                self.base_url, self.admin_email, self.admin_password
            )
            if auth_result["success"]:
                self.admin_token = auth_result["token"]
                logger.info("   ✅ Admin authenticated")
            else:
                logger.warning(f"   ⚠️ Admin auth failed: {auth_result.get('error')}")
        except Exception as auth_err:
            logger.warning(f"   ⚠️ Admin auth error (non-fatal): {auth_err}")

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

        # 4.5 Build scenario details for feedback agent
        scenario_details = []
        for sc, res in zip(scenarios, results):
            scenario_details.append({
                "name": sc["name"],
                "status": res["status"],
                "duration_ms": res.get("duration_ms", 0),
                "error_message": res.get("error"),
                "type": sc.get("type", "api"),
            })

        # 5. Generate reports (pass version info + scenario details)
        report = self.reporter.report(
            suite_result,
            version_info=version_info,
            scenario_details=scenario_details,
        )

        logger.info(f"\n{report['summary']}")
        return report

    async def _check_service_health(self, base_url: str, path: str = "/healthz") -> bool:
        """Check if a service is reachable. Returns True if healthy."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{base_url}{path}")
                return resp.status_code < 500
        except Exception:
            # Try /health as fallback
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(f"{base_url}/health")
                    return resp.status_code < 500
            except Exception:
                return False

    def _build_suite_result(
        self,
        scenarios: list[dict],
        results: list[dict],
        yaml_path: str,
    ) -> TestSuiteResult:
        """Convert run results into TestSuiteResult for reporting."""
        script = TestScript(
            name=self.get_suite_name(yaml_path),
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
