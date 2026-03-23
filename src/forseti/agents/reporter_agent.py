"""ReporterAgent — Sprint 03 / Sprint 34.

Generates reports, saves to SQLite, builds GitHub issue summaries,
and posts issues to the correct project repo via GitHub API.
Designed to run AFTER all tests complete (not during).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import httpx

from forseti.db.results_db import ResultsDB
from forseti.models import TestSuiteResult, TestStatus
from forseti.reporter.iso_report import ISOReportGenerator

logger = logging.getLogger("forseti.agents.reporter")


class ReporterAgent:
    """Agent that handles all reporting after a test run completes.

    Responsibilities:
    1. Save results to SQLite database
    2. Generate ISO SI-04 markdown report
    3. Generate human-readable summary
    4. Build GitHub issue body (only if failures exist)
    """

    def __init__(
        self,
        db: ResultsDB,
        report_dir: str = "reports",
        github_repo: str = "",
    ):
        self.db = db
        self.report_dir = report_dir
        self.iso_gen = ISOReportGenerator()
        # e.g. "MegaWiz-Dev-Team/Eir" — comes from forseti.yaml github.repo
        self.github_repo = github_repo

    def report(
        self,
        result: TestSuiteResult,
        version_info: dict | None = None,
        scenario_details: list[dict] | None = None,
    ) -> dict:
        """Full report pipeline: DB + ISO + Summary + Feedback.

        Returns:
            {"run_id": int, "iso_report_path": str, "summary": str,
             "github_issue": tuple | None, "version_info": dict,
             "feedback": dict | None, "feedback_report_path": str | None}
        """
        vi = version_info or {"version": "unknown", "commit": "unknown"}
        run_id = self.save_to_db(result, version_info=vi)
        iso_path = self.generate_iso_report(result)
        summary = self.generate_summary(result)
        issue = self.build_github_issue(result)

        # Generate LLM feedback (optional — graceful fallback)
        feedback = None
        feedback_path = None
        try:
            feedback, feedback_path = self._generate_feedback(
                result, run_id, vi, scenario_details,
            )
        except Exception as e:
            logger.warning(f"⚠️ Feedback generation skipped: {e}")

        # Post to Forseti dashboard
        self.post_to_dashboard(result, vi)

        # Post GitHub issue to the correct project repo (only on failures)
        github_issue_url = None
        if issue:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._post_github_issue_async(*issue))
                        github_issue_url = future.result(timeout=15)
                else:
                    github_issue_url = asyncio.run(self._post_github_issue_async(*issue))
            except Exception as e:
                logger.warning(f"⚠️ GitHub issue posting skipped: {e}")

        if github_issue_url:
            logger.info(f"🐛 GitHub Issue: {github_issue_url}")

        logger.info(f"📊 Report complete — Run #{run_id}")
        logger.info(f"   ISO: {iso_path}")
        logger.info(f"   {summary}")

        return {
            "run_id": run_id,
            "iso_report_path": str(iso_path),
            "summary": summary,
            "github_issue": issue,
            "github_issue_url": github_issue_url,
            "version_info": vi,
            "feedback": feedback,
            "feedback_report_path": feedback_path,
        }

    def _generate_feedback(
        self,
        result: TestSuiteResult,
        run_id: int,
        version_info: dict,
        scenario_details: list[dict] | None,
    ) -> tuple[dict, str]:
        """Call FeedbackAgent, save to DB, generate markdown report."""
        from forseti.agents.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()

        # Build scenario detail list for LLM context
        sc_details = scenario_details or []
        if not sc_details:
            for sr in result.scenario_results:
                sc_details.append({
                    "name": sr.scenario.name,
                    "status": sr.status.value,
                    "duration_ms": sr.duration_ms,
                    "error_message": sr.error_message,
                    "type": "ui" if sr.scenario.tags and "ui" in sr.scenario.tags else "api",
                })

        feedback = agent.analyze(
            suite_name=result.script.name,
            base_url=result.script.base_url,
            pass_rate=result.pass_rate,
            passed=result.passed,
            total=result.total,
            duration_ms=result.duration_ms,
            scenarios=sc_details,
            version=version_info.get("version", "unknown"),
        )

        # Save to DB
        self.db.save_feedback(run_id, "backend", feedback.get("backend", []))
        self.db.save_feedback(run_id, "ui", feedback.get("ui", []))

        # Generate markdown report
        feedback_path = agent.generate_feedback_report(
            feedback, result.script.name, run_id,
            output_dir=str(Path(self.report_dir) / "feedback"),
        )

        return feedback, feedback_path

    def save_to_db(self, result: TestSuiteResult, version_info: dict | None = None) -> int:
        """Save test results to SQLite database."""
        vi = version_info or {"version": "unknown", "commit": "unknown"}
        run_id = self.db.save_run(
            suite_name=result.script.name,
            phase=result.script.phase.value,
            base_url=result.script.base_url,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            errors=result.errors,
            skipped=result.skipped,
            duration_ms=result.duration_ms,
            project_version=vi.get("version", "unknown"),
            project_commit=vi.get("commit", "unknown"),
        )

        for sr in result.scenario_results:
            self.db.save_scenario(
                run_id=run_id,
                name=sr.scenario.name,
                status=sr.status.value,
                duration_ms=sr.duration_ms,
                error_message=sr.error_message,
            )

        logger.info(f"💾 Saved to SQLite: Run #{run_id}")
        return run_id

    def post_to_dashboard(self, result: TestSuiteResult, version_info: dict) -> None:
        """Post results to the Forseti Dashboard API."""
        forseti_url = os.getenv("FORSETI_URL", "http://localhost:5555")
        endpoint = f"{forseti_url}/api/runs"
        
        scenarios = []
        for sr in result.scenario_results:
            scenarios.append({
                "name": sr.scenario.name,
                "status": sr.status.value,
                "duration_ms": sr.duration_ms,
                "error_message": sr.error_message,
            })
            
        payload = {
            "suite_name": result.script.name,
            "phase": "SIT",
            "base_url": result.script.base_url,
            "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "skipped": result.skipped,
            "duration_ms": result.duration_ms,
            "project_version": version_info.get("version", "unknown"),
            "project_commit": version_info.get("commit", "unknown"),
            "scenarios": scenarios
        }
        
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(endpoint, json=payload)
                if res.status_code == 201:
                    data = res.json()
                    logger.info(f"🚀 Published to Forseti Dashboard: Run #{data.get('id')}")
                else:
                    logger.warning(f"⚠️ Failed to publish to Forseti: HTTP {res.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not reach Forseti Dashboard at {endpoint}: {e}")

    def generate_iso_report(self, result: TestSuiteResult) -> Path:
        """Generate ISO SI-04 markdown report."""
        return self.iso_gen.save(result, output_dir=self.report_dir)

    def generate_summary(self, result: TestSuiteResult) -> str:
        """Generate human-readable summary string."""
        return (
            f"⚖️ Forseti — {result.script.name}\n"
            f"   ✅ {result.passed}/{result.total} passed "
            f"({result.pass_rate:.0f}%) | "
            f"❌ {result.failed} failed | "
            f"⏱️ {result.duration_ms}ms"
        )

    def build_github_issue(self, result: TestSuiteResult) -> tuple[str, str] | None:
        """Build GitHub issue title + body for failures.

        Returns None if all tests passed (no issue needed).
        """
        if result.failed == 0 and result.errors == 0:
            return None

        title = (
            f"⚖️ [Forseti] E2E Results: "
            f"{result.passed}/{result.total} passed — "
            f"{result.script.name}"
        )

        lines = [
            "## ⚖️ Forseti E2E Test Results",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Suite | {result.script.name} |",
            f"| Phase | {result.script.phase.value} |",
            f"| URL | {result.script.base_url} |",
            f"| Pass Rate | **{result.pass_rate:.0f}%** |",
            f"| Total | {result.total} |",
            f"| ✅ Passed | {result.passed} |",
            f"| ❌ Failed | {result.failed} |",
            f"| ⚠️ Errors | {result.errors} |",
            "",
            "## Failed Scenarios",
            "",
        ]

        for sr in result.scenario_results:
            if sr.status in (TestStatus.FAIL, TestStatus.ERROR):
                icon = "❌" if sr.status == TestStatus.FAIL else "⚠️"
                lines.append(f"- {icon} **{sr.scenario.name}**: {sr.error_message or 'No details'}")

        lines.append("")
        lines.append(f"*Generated by Forseti ⚖️ at {datetime.now().isoformat()}*")

        return title, "\n".join(lines)

    async def _post_github_issue_async(self, title: str, body: str) -> str | None:
        """Post a GitHub Issue to the project-specific repo via GitHub REST API.

        Uses:
          - self.github_repo  → set from forseti.yaml github.repo (e.g. "Owner/Repo")
          - GITHUB_TOKEN env  → personal access token or Actions token

        Returns the created issue URL, or None if skipped/failed.
        """
        token = os.environ.get("GITHUB_TOKEN", "")
        repo = self.github_repo

        if not token:
            logger.warning("⚠️ GITHUB_TOKEN not set — skipping GitHub issue creation")
            return None
        if not repo:
            logger.warning("⚠️ github_repo not configured — skipping GitHub issue creation")
            return None
        if "/" not in repo:
            logger.error(f"❌ Invalid github_repo format '{repo}' — expected 'owner/repo'")
            return None

        owner, repo_name = repo.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {"title": title, "body": body, "labels": ["bug", "e2e-test-failure"]}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 201:
                    issue_url = resp.json().get("html_url", "")
                    logger.info(f"✅ Issue created: {issue_url}")
                    return issue_url
                else:
                    logger.warning(
                        f"⚠️ GitHub API returned {resp.status_code}: {resp.text[:200]}"
                    )
                    return None
        except Exception as e:
            logger.warning(f"⚠️ GitHub issue creation failed: {e}")
            return None
