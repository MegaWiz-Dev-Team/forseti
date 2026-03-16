"""YAML test script parser."""

from __future__ import annotations

from pathlib import Path

import yaml

from forseti.models import TestScript, TestScenario, TestStep


def parse_script(path: str | Path) -> TestScript:
    """Parse a YAML test script file into a TestScript model.

    Args:
        path: Path to the YAML test script file.

    Returns:
        Validated TestScript object.

    Raises:
        FileNotFoundError: If the script file doesn't exist.
        ValueError: If the script is invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Test script not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid test script format in {path}: expected a YAML mapping")

    # Normalize steps: support both string shorthand and dict form
    scenarios = []
    for sc_raw in raw.get("scenarios", []):
        steps = []
        for step_raw in sc_raw.get("steps", []):
            if isinstance(step_raw, str):
                steps.append(TestStep(action=step_raw))
            elif isinstance(step_raw, dict):
                steps.append(TestStep(**step_raw))
            else:
                raise ValueError(f"Invalid step format: {step_raw}")

        scenarios.append(
            TestScenario(
                name=sc_raw["name"],
                steps=steps,
                expected=sc_raw.get("expected", ""),
                tags=sc_raw.get("tags", []),
            )
        )

    return TestScript(
        name=raw.get("name", path.stem),
        base_url=raw.get("base_url", ""),
        phase=raw.get("phase", "SIT"),
        scenarios=scenarios,
        metadata=raw.get("metadata", {}),
    )


def validate_script(path: str | Path) -> list[str]:
    """Validate a test script and return a list of issues.

    Returns:
        Empty list if valid, or list of error messages.
    """
    issues: list[str] = []
    try:
        script = parse_script(path)
    except Exception as e:
        return [str(e)]

    if not script.name:
        issues.append("Missing 'name' field")
    if not script.base_url:
        issues.append("Missing 'base_url' field")
    if not script.scenarios:
        issues.append("No scenarios defined")

    for i, sc in enumerate(script.scenarios):
        if not sc.name:
            issues.append(f"Scenario {i}: missing 'name'")
        if not sc.steps:
            issues.append(f"Scenario '{sc.name}': no steps defined")
        if not sc.expected:
            issues.append(f"Scenario '{sc.name}': missing 'expected' result")

    return issues
