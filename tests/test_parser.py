"""Tests for Forseti YAML parser."""

import pytest
import tempfile
from pathlib import Path

from forseti.parser import parse_script, validate_script


VALID_SCRIPT = """\
name: "Login Test"
base_url: "https://example.com"
phase: "SIT"

scenarios:
  - name: "Happy Login"
    steps:
      - action: "กรอก username ว่า admin"
      - action: "กรอก password ว่า pass123"
      - action: "กดปุ่ม Login"
    expected: "เห็นหน้า Dashboard"
"""

SHORTHAND_SCRIPT = """\
name: "Shorthand Test"
base_url: "https://example.com"

scenarios:
  - name: "Test 1"
    steps:
      - "click the button"
      - "type hello"
    expected: "see result"
"""

INVALID_SCRIPT = """\
not_a_list: true
"""


class TestParseScript:
    def test_parse_valid_script(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(VALID_SCRIPT, encoding="utf-8")
        script = parse_script(f)
        assert script.name == "Login Test"
        assert script.base_url == "https://example.com"
        assert script.phase.value == "SIT"
        assert len(script.scenarios) == 1
        assert len(script.scenarios[0].steps) == 3
        assert script.scenarios[0].steps[0].action == "กรอก username ว่า admin"

    def test_parse_shorthand_steps(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(SHORTHAND_SCRIPT, encoding="utf-8")
        script = parse_script(f)
        assert len(script.scenarios[0].steps) == 2
        assert script.scenarios[0].steps[0].action == "click the button"

    def test_parse_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_script("/nonexistent/path.yaml")

    def test_parse_invalid_format(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("just a string", encoding="utf-8")
        with pytest.raises(ValueError, match="expected a YAML mapping"):
            parse_script(f)


class TestValidateScript:
    def test_valid_script(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(VALID_SCRIPT, encoding="utf-8")
        issues = validate_script(f)
        assert issues == []

    def test_missing_base_url(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(
            "name: Test\nscenarios:\n  - name: S1\n    steps:\n      - action: click\n    expected: ok\n",
            encoding="utf-8",
        )
        issues = validate_script(f)
        assert any("base_url" in i for i in issues)

    def test_empty_scenarios(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(
            "name: Test\nbase_url: http://localhost\nscenarios: []\n",
            encoding="utf-8",
        )
        issues = validate_script(f)
        assert any("No scenarios" in i for i in issues)

    def test_missing_expected(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text(
            "name: Test\nbase_url: http://localhost\nscenarios:\n  - name: S1\n    steps:\n      - action: click\n",
            encoding="utf-8",
        )
        issues = validate_script(f)
        assert any("expected" in i for i in issues)
