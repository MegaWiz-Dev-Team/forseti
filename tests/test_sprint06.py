"""TDD Tests for Sprint 06 — Version Policy + LLM Feedback.

Red → Green: Tests first, implementation second.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch



# ─── 6A: Version Policy ─────────────────────────────────────────────


class TestSemVerParser:
    """Tests for _parse_semver utility."""

    def test_parse_standard_tag(self):
        from forseti.tools.version_detector import _parse_semver
        assert _parse_semver("v2.1.3") == (2, 1, 3)

    def test_parse_no_v_prefix(self):
        from forseti.tools.version_detector import _parse_semver
        assert _parse_semver("1.0.0") == (1, 0, 0)

    def test_parse_invalid(self):
        from forseti.tools.version_detector import _parse_semver
        assert _parse_semver("latest") == (0, 0, 0)


class TestSuggestNextVersion:
    """Tests for suggest_next_version()."""

    def test_suggest_from_forseti_repo(self):
        """Suggest version from Forseti's own repo (real git)."""
        from forseti.tools.version_detector import suggest_next_version
        result = suggest_next_version(
            project_dir=str(Path(__file__).parent.parent)
        )
        assert "current" in result
        assert "suggested" in result
        assert "bump" in result
        assert "reason" in result
        assert "commits" in result

    def test_suggest_none_dir(self):
        """None project_dir returns initial version."""
        from forseti.tools.version_detector import suggest_next_version
        result = suggest_next_version(project_dir=None)
        assert result["suggested"] == "v0.1.0"

    def test_suggest_non_git_dir(self):
        """Non-git dir returns initial version."""
        from forseti.tools.version_detector import suggest_next_version
        with tempfile.TemporaryDirectory() as tmpdir:
            result = suggest_next_version(project_dir=tmpdir)
            assert result["current"] == "none"
            assert result["suggested"] == "v0.1.0"


class TestCreateVersionTag:
    """Tests for create_version_tag()."""

    def test_create_tag_non_git_dir(self):
        """Fails gracefully in non-git dir."""
        from forseti.tools.version_detector import create_version_tag
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_version_tag(tmpdir, "v1.0.0")
            assert result["success"] is False


# ─── 6B: LLM Feedback Agent ─────────────────────────────────────────


class TestFeedbackAgentStructure:
    """Tests for FeedbackAgent class structure."""

    def test_agent_init(self):
        """FeedbackAgent initializes with model and api_key."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(model="gemini-2.0-flash", api_key="test-key")
        assert agent.model == "gemini-2.0-flash"
        assert agent.api_key == "test-key"

    def test_format_scenario_details(self):
        """Scenario details formatted as readable text."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")
        scenarios = [
            {"name": "Login", "status": "pass", "duration_ms": 100, "type": "ui"},
            {"name": "API Health", "status": "fail", "duration_ms": 50,
             "error_message": "timeout", "type": "api"},
        ]
        text = agent._format_scenario_details(scenarios)
        assert "Login" in text
        assert "API Health" in text
        assert "timeout" in text

    def test_parse_feedback_json_valid(self):
        """Valid JSON array is parsed correctly."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")
        json_text = '[{"category":"coverage","severity":"high","suggestion":"Add auth tests","scenario":"general"}]'
        result = agent._parse_feedback_json(json_text)
        assert len(result) == 1
        assert result[0]["category"] == "coverage"

    def test_parse_feedback_json_code_block(self):
        """JSON inside markdown code block is parsed."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")
        text = '```json\n[{"category":"performance","severity":"low","suggestion":"OK","scenario":"general"}]\n```'
        result = agent._parse_feedback_json(text)
        assert len(result) == 1
        assert result[0]["category"] == "performance"

    def test_parse_feedback_json_invalid(self):
        """Invalid JSON returns fallback item."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")
        result = agent._parse_feedback_json("not json at all")
        assert len(result) == 1
        assert result[0]["category"] == "general"

    def test_detect_test_types(self):
        """Test types are detected from scenarios."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")
        scenarios = [
            {"type": "api"},
            {"type": "ui"},
            {"type": "api"},
        ]
        types = agent._detect_test_types(scenarios)
        assert "api" in types
        assert "ui" in types


class TestFeedbackAgentAnalyze:
    """Tests for FeedbackAgent.analyze() with mocked LLM."""

    def test_analyze_returns_both_perspectives(self):
        """analyze() returns backend + ui feedback."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")

        mock_response = '[{"category":"coverage","severity":"high","suggestion":"Add more tests","scenario":"general"}]'

        with patch.object(agent, '_call_llm', return_value=mock_response):
            result = agent.analyze(
                suite_name="Test Suite",
                base_url="http://localhost",
                pass_rate=100.0,
                passed=3,
                total=3,
                duration_ms=1000,
                scenarios=[
                    {"name": "Login", "status": "pass", "duration_ms": 500, "type": "ui"},
                ],
            )

        assert "backend" in result
        assert "ui" in result
        assert len(result["backend"]) >= 1
        assert len(result["ui"]) >= 1
        assert "generated_at" in result


class TestFeedbackReport:
    """Tests for feedback markdown report generation."""

    def test_generate_feedback_report(self):
        """Generates markdown report file."""
        from forseti.agents.feedback_agent import FeedbackAgent
        agent = FeedbackAgent(api_key="test")

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback = {
                "backend": [{"category": "coverage", "severity": "high",
                             "suggestion": "Add auth tests", "scenario": "general"}],
                "ui": [{"category": "accessibility", "severity": "medium",
                        "suggestion": "Add ARIA labels", "scenario": "Login"}],
                "generated_at": "2026-03-18T07:00:00",
            }

            path = agent.generate_feedback_report(
                feedback, "Test Suite", run_id=1, output_dir=tmpdir,
            )
            assert Path(path).exists()
            content = Path(path).read_text()
            assert "Backend Expert" in content
            assert "UX/UI Expert" in content
            assert "Add auth tests" in content


# ─── 6B2: Feedback in DB ────────────────────────────────────────────


class TestFeedbackDB:
    """Tests for feedback table in ResultsDB."""

    def test_save_and_get_feedback(self):
        """Save feedback items and retrieve by run_id."""
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            run_id = db.save_run(
                suite_name="Test", phase="SIT", base_url="http://localhost",
                total=1, passed=1, failed=0, errors=0, skipped=0,
                duration_ms=100,
            )

            items = [
                {"category": "coverage", "severity": "high",
                 "suggestion": "Add auth tests", "scenario": "Login"},
                {"category": "performance", "severity": "low",
                 "suggestion": "Response times OK", "scenario": "general"},
            ]

            count = db.save_feedback(run_id, "backend", items)
            assert count == 2

            feedback = db.get_feedback(run_id)
            assert len(feedback) == 2
            assert feedback[0]["perspective"] == "backend"
            assert feedback[0]["category"] == "coverage"
            assert feedback[1]["suggestion"] == "Response times OK"
            db.close()

    def test_get_feedback_empty(self):
        """No feedback returns empty list."""
        from forseti.db.results_db import ResultsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = ResultsDB(db_path=f"{tmpdir}/test.db")
            feedback = db.get_feedback(999)
            assert feedback == []
            db.close()
