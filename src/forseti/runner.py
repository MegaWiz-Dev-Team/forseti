"""Main test runner — orchestrates the full Forseti test execution pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

from forseti.agent.executor import ActionExecutor
from forseti.agent.llm import create_llm_client
from forseti.browser.engine import BrowserEngine
from forseti.config import ForsetiConfig
from forseti.models import (
    ScenarioResult,
    TestScript,
    TestStatus,
    TestSuiteResult,
)
from forseti.reporter.collector import ResultCollector
from forseti.reporter.github_issue import GitHubIssueReporter
from forseti.reporter.html_report import HTMLReportGenerator

logger = logging.getLogger("forseti.runner")


class ForsetiRunner:
    """Orchestrates the entire test execution pipeline.

    Pipeline:
        1. Parse test script (already done before runner)
        2. Start browser
        3. For each scenario:
           a. LLM translates each step → ActionPlan
           b. Executor runs actions on Playwright page
           c. LLM checks assertion (expected result)
           d. Collect result
        4. Generate reports
        5. Create GitHub issues for failures
    """

    def __init__(self, config: ForsetiConfig):
        self.config = config
        self.llm = create_llm_client(config.llm)
        self.engine = BrowserEngine(config.browser)
        self.collector = ResultCollector(config.report.results_dir)
        self.html_reporter = HTMLReportGenerator(
            output_dir=config.report.output_dir,
        )
        self.github_reporter = GitHubIssueReporter(config.github)

    async def run(self, script: TestScript, dry_run: bool = False) -> TestSuiteResult:
        """Execute a full test suite.

        Args:
            script: Parsed test script.
            dry_run: If True, only generate action plans without executing.

        Returns:
            Complete test suite result.
        """
        suite_result = TestSuiteResult(script=script, started_at=datetime.now())

        logger.info(f"⚖️  Forseti — Starting test suite: {script.name}")
        logger.info(f"   Phase: {script.phase.value}")
        logger.info(f"   Target: {script.base_url}")
        logger.info(f"   Scenarios: {len(script.scenarios)}")
        logger.info("")

        if dry_run:
            suite_result = await self._dry_run(script, suite_result)
        else:
            suite_result = await self._full_run(script, suite_result)

        suite_result.finished_at = datetime.now()

        # Generate reports
        self._generate_reports(suite_result)

        # Create GitHub issues for failures
        if self.config.github.enabled:
            self.github_reporter.report_failures(suite_result)

        # Print summary
        self._print_summary(suite_result)

        return suite_result

    async def _full_run(
        self, script: TestScript, suite_result: TestSuiteResult
    ) -> TestSuiteResult:
        """Full run: LLM + Browser execution."""
        screenshots_dir = Path(self.config.report.screenshots_dir)

        await self.engine.start()
        try:
            for i, scenario in enumerate(script.scenarios):
                logger.info(f"📋 Scenario {i + 1}/{len(script.scenarios)}: {scenario.name}")
                sc_result = ScenarioResult(scenario=scenario, started_at=datetime.now())
                start = time.monotonic()

                async with self.engine.session() as page:
                    # Navigate to base URL first
                    await page.goto(script.base_url, wait_until="domcontentloaded")

                    executor = ActionExecutor(
                        page=page,
                        screenshots_dir=screenshots_dir,
                        timeout_ms=self.config.browser.timeout_ms,
                    )

                    # Execute each step
                    all_steps_passed = True
                    for j, step in enumerate(scenario.steps):
                        logger.info(f"  Step {j + 1}: {step.action}")

                        # LLM: translate step → action plan
                        plan = await self.llm.generate_actions(step.action, script.base_url)
                        logger.info(f"    → {len(plan.actions)} actions planned")

                        # Execute the plan
                        step_result = await executor.execute_plan(
                            plan, step, scenario.name, j
                        )
                        sc_result.step_results.append(step_result)

                        if step_result.status != TestStatus.PASS:
                            all_steps_passed = False
                            logger.warning(f"    ❌ Step failed: {step_result.error_message}")
                            break  # Stop scenario on first failure

                    # Check assertion (expected result) if all steps passed
                    if all_steps_passed and scenario.expected:
                        logger.info(f"  🔍 Checking assertion: {scenario.expected}")
                        page_content = await page.content()
                        page_text = await page.evaluate("() => document.body.innerText")

                        assertion = await self.llm.check_assertion(
                            scenario.expected, page_text[:8000]
                        )

                        if assertion.get("passed", False):
                            sc_result.status = TestStatus.PASS
                            sc_result.assertion_result = assertion.get("reason", "Passed")
                            logger.info(f"  ✅ Assertion passed: {assertion.get('reason', '')}")
                        else:
                            sc_result.status = TestStatus.FAIL
                            sc_result.assertion_result = assertion.get("reason", "Failed")
                            sc_result.error_message = assertion.get("reason", "Assertion failed")
                            logger.warning(f"  ❌ Assertion failed: {assertion.get('reason', '')}")
                    elif not all_steps_passed:
                        sc_result.status = TestStatus.ERROR
                        sc_result.error_message = "Step execution failed"

                sc_result.duration_ms = int((time.monotonic() - start) * 1000)
                sc_result.finished_at = datetime.now()
                suite_result.scenario_results.append(sc_result)
                logger.info("")

        finally:
            await self.engine.stop()

        return suite_result

    async def _dry_run(
        self, script: TestScript, suite_result: TestSuiteResult
    ) -> TestSuiteResult:
        """Dry run: only generate action plans, no browser execution."""
        logger.info("🏜️  DRY RUN MODE — No browser will be launched\n")

        for i, scenario in enumerate(script.scenarios):
            logger.info(f"📋 Scenario {i + 1}/{len(script.scenarios)}: {scenario.name}")
            sc_result = ScenarioResult(scenario=scenario, started_at=datetime.now())

            for j, step in enumerate(scenario.steps):
                logger.info(f"  Step {j + 1}: {step.action}")
                plan = await self.llm.generate_actions(step.action, script.base_url)

                for k, action in enumerate(plan.actions):
                    logger.info(
                        f"    → [{action.type}] {action.description} "
                        f"(selector={action.selector}, value={action.value})"
                    )

            sc_result.status = TestStatus.SKIP
            sc_result.finished_at = datetime.now()
            suite_result.scenario_results.append(sc_result)
            logger.info(f"  ⏭️  Skipped (dry run)\n")

        return suite_result

    def _generate_reports(self, result: TestSuiteResult) -> None:
        """Generate JSON and HTML reports."""
        # JSON
        if self.config.report.json_report:
            self.collector.save_json(result)

        # HTML
        if self.config.report.html_report:
            self.html_reporter.generate(result)

    def _print_summary(self, result: TestSuiteResult) -> None:
        """Print a summary to the console."""
        logger.info("=" * 60)
        logger.info(f"⚖️  Forseti — Test Suite Complete: {result.script.name}")
        logger.info(f"   Phase: {result.script.phase.value}")
        logger.info(f"   Total: {result.total}  |  "
                     f"✅ Pass: {result.passed}  |  "
                     f"❌ Fail: {result.failed}  |  "
                     f"⚠️  Error: {result.errors}  |  "
                     f"⏭️  Skip: {result.skipped}")
        logger.info(f"   Pass Rate: {result.pass_rate:.1f}%")
        logger.info(f"   Duration: {result.duration_ms}ms")
        logger.info("=" * 60)
