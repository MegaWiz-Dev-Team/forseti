"""Tests for Forseti models."""

import pytest
from forseti.models import (
    ActionPlan,
    BrowserAction,
    ScenarioResult,
    TestPhase,
    TestScript,
    TestScenario,
    TestStatus,
    TestStep,
    TestSuiteResult,
)


class TestTestStep:
    def test_create_step_with_action(self):
        step = TestStep(action="กรอก username ว่า admin")
        assert step.action == "กรอก username ว่า admin"
        assert step.screenshot is True  # default

    def test_create_step_no_screenshot(self):
        step = TestStep(action="wait 2 seconds", screenshot=False)
        assert step.screenshot is False


class TestTestScenario:
    def test_create_scenario(self):
        sc = TestScenario(
            name="Login Test",
            steps=[TestStep(action="click login")],
            expected="see dashboard",
        )
        assert sc.name == "Login Test"
        assert len(sc.steps) == 1
        assert sc.expected == "see dashboard"
        assert sc.tags == []

    def test_scenario_with_tags(self):
        sc = TestScenario(
            name="Login",
            steps=[TestStep(action="click")],
            expected="ok",
            tags=["smoke", "login"],
        )
        assert sc.tags == ["smoke", "login"]


class TestTestScript:
    def test_create_script(self):
        script = TestScript(
            name="My Suite",
            base_url="https://example.com",
            scenarios=[
                TestScenario(
                    name="Test 1",
                    steps=[TestStep(action="go to page")],
                    expected="page loads",
                )
            ],
        )
        assert script.name == "My Suite"
        assert script.phase == TestPhase.SIT
        assert len(script.scenarios) == 1

    def test_script_phases(self):
        for phase in ["SIT", "UAT", "REGRESSION"]:
            script = TestScript(
                name="Test",
                base_url="http://localhost",
                phase=phase,
                scenarios=[],
            )
            assert script.phase == TestPhase(phase)


class TestBrowserAction:
    def test_navigate_action(self):
        action = BrowserAction(
            type="navigate",
            value="https://example.com",
            description="Go to homepage",
        )
        assert action.type == "navigate"
        assert action.selector is None
        assert action.value == "https://example.com"

    def test_click_action(self):
        action = BrowserAction(
            type="click",
            selector="button#login",
            description="Click login button",
        )
        assert action.type == "click"
        assert action.selector == "button#login"


class TestActionPlan:
    def test_create_plan(self):
        plan = ActionPlan(
            step_description="กดปุ่ม Login",
            actions=[
                BrowserAction(type="click", selector="button", description="click"),
            ],
        )
        assert plan.step_description == "กดปุ่ม Login"
        assert len(plan.actions) == 1


class TestTestSuiteResult:
    def _make_result(self, statuses: list[TestStatus]) -> TestSuiteResult:
        script = TestScript(name="Test", base_url="http://localhost", scenarios=[])
        result = TestSuiteResult(script=script)
        for status in statuses:
            sc = TestScenario(name="sc", steps=[], expected="ok")
            sc_result = ScenarioResult(scenario=sc, status=status)
            result.scenario_results.append(sc_result)
        return result

    def test_all_pass(self):
        result = self._make_result([TestStatus.PASS, TestStatus.PASS, TestStatus.PASS])
        assert result.total == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.pass_rate == 100.0

    def test_mixed_results(self):
        result = self._make_result([TestStatus.PASS, TestStatus.FAIL, TestStatus.ERROR])
        assert result.total == 3
        assert result.passed == 1
        assert result.failed == 1
        assert result.errors == 1
        assert result.pass_rate == pytest.approx(33.3, abs=0.1)

    def test_empty_results(self):
        result = self._make_result([])
        assert result.total == 0
        assert result.pass_rate == 0.0

    def test_all_fail(self):
        result = self._make_result([TestStatus.FAIL, TestStatus.FAIL])
        assert result.passed == 0
        assert result.pass_rate == 0.0
