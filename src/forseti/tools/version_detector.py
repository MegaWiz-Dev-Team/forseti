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


def _run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run a git command, returning CompletedProcess."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _parse_semver(tag: str) -> tuple[int, int, int]:
    """Parse 'v1.2.3' or '1.2.3' into (1, 2, 3)."""
    clean = tag.lstrip("v")
    parts = clean.split(".")
    if len(parts) != 3:
        return (0, 0, 0)
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return (0, 0, 0)


def suggest_next_version(project_dir: str | None = None) -> dict:
    """Analyze git log since last tag and suggest next SemVer version.

    Rules (Conventional Commits):
    - BREAKING CHANGE or '!:' → MAJOR bump
    - 'feat:' commit → MINOR bump
    - 'fix:' commit → PATCH bump
    - No conventional prefix → PATCH bump

    Returns:
        {"current": "v2.1.0", "suggested": "v2.2.0",
         "bump": "minor", "reason": "...", "commits": [...]}
    """
    result = {
        "current": "none",
        "suggested": "v0.1.0",
        "bump": "minor",
        "reason": "No tags found — initial version",
        "commits": [],
    }

    if not project_dir:
        return result

    git_dir = Path(project_dir)
    if not (git_dir / ".git").exists():
        return result

    cwd = str(git_dir)

    # Get latest tag
    tag_result = _run_git(["describe", "--tags", "--abbrev=0"], cwd)
    current_tag = tag_result.stdout.strip() if tag_result.returncode == 0 else ""

    if not current_tag:
        # No tags — get all commits
        log_result = _run_git(["log", "--oneline", "-20"], cwd)
        commits = log_result.stdout.strip().splitlines() if log_result.returncode == 0 else []
        result["commits"] = commits
        return result

    result["current"] = current_tag
    major, minor, patch = _parse_semver(current_tag)

    # Get commits since last tag
    log_result = _run_git(
        ["log", f"{current_tag}..HEAD", "--oneline"],
        cwd,
    )
    if log_result.returncode != 0 or not log_result.stdout.strip():
        result["suggested"] = current_tag
        result["bump"] = "none"
        result["reason"] = "No new commits since last tag"
        return result

    commits = log_result.stdout.strip().splitlines()
    result["commits"] = commits

    # Analyze commit messages for SemVer bump
    has_breaking = False
    has_feat = False
    has_fix = False

    for commit in commits:
        msg = commit.split(" ", 1)[1] if " " in commit else commit
        msg_lower = msg.lower()
        if "breaking change" in msg_lower or "!:" in msg:
            has_breaking = True
        elif msg_lower.startswith("feat"):
            has_feat = True
        elif msg_lower.startswith("fix"):
            has_fix = True

    if has_breaking:
        result["suggested"] = f"v{major + 1}.0.0"
        result["bump"] = "major"
        result["reason"] = f"Breaking change detected in {len(commits)} commit(s)"
    elif has_feat:
        result["suggested"] = f"v{major}.{minor + 1}.0"
        result["bump"] = "minor"
        result["reason"] = f"New feature(s) in {len(commits)} commit(s)"
    elif has_fix:
        result["suggested"] = f"v{major}.{minor}.{patch + 1}"
        result["bump"] = "patch"
        result["reason"] = f"Bug fix(es) in {len(commits)} commit(s)"
    else:
        result["suggested"] = f"v{major}.{minor}.{patch + 1}"
        result["bump"] = "patch"
        result["reason"] = f"{len(commits)} commit(s) since {current_tag}"

    return result


def create_version_tag(
    project_dir: str,
    version: str,
    message: str | None = None,
) -> dict[str, bool | str]:
    """Create a git tag in the project directory.

    Args:
        project_dir: Path to git repo.
        version: Tag name, e.g. "v2.2.0".
        message: Optional tag message (creates annotated tag).

    Returns:
        {"success": True/False, "tag": "v2.2.0", "error": "..."}
    """
    cwd = str(Path(project_dir))

    if message:
        cmd = ["tag", "-a", version, "-m", message]
    else:
        cmd = ["tag", version]

    try:
        result = _run_git(cmd, cwd)
        if result.returncode == 0:
            return {"success": True, "tag": version, "error": ""}
        return {"success": False, "tag": version, "error": result.stderr.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"success": False, "tag": version, "error": str(e)}
