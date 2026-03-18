"""Version detector — auto-detect project version from Git.

Reads git commit SHA and latest tag from a project directory.
Used by Forseti orchestrator to track which version was tested.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def detect_project_version(
    project_dir: str | None = None,
    github_repo: str | None = None,
) -> dict[str, str]:
    """Detect version info from a git repository.

    Tries (in order):
    1. git describe --tags  → version tag (e.g. "v2.1.0")
    2. git rev-parse --short HEAD  → commit SHA (e.g. "c825675")
    3. Fallback to "unknown"

    Args:
        project_dir: Local path to the project git repo.
        github_repo: GitHub repo (owner/name) for future remote detection.

    Returns:
        {"version": "v2.1.0", "commit": "c825675"}
    """
    result = {"version": "unknown", "commit": "unknown"}

    if not project_dir:
        return result

    git_dir = Path(project_dir)
    if not (git_dir / ".git").exists():
        return result

    # Get commit SHA
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(git_dir),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if sha.returncode == 0:
            result["commit"] = sha.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Get version tag
    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=str(git_dir),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if tag.returncode == 0:
            result["version"] = tag.stdout.strip()
        else:
            # No tags — use commit as version
            result["version"] = result["commit"]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return result
