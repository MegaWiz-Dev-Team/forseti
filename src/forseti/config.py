"""Configuration management for Forseti."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(default="gemini", description="LLM provider: gemini or openai_compatible")
    model: str = Field(default="gemini-2.0-flash", description="Model name")
    api_key: str = Field(default="", description="API key (or set GEMINI_API_KEY env var)")
    base_url: str | None = Field(
        default=None, description="Base URL for self-hosted LLM (OpenAI-compatible)"
    )
    temperature: float = Field(default=0.1, description="LLM temperature for action generation")
    max_tokens: int = Field(default=4096, description="Max output tokens")


class BrowserConfig(BaseModel):
    """Browser configuration."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_type: str = Field(default="chromium", description="chromium, firefox, or webkit")
    viewport_width: int = Field(default=1280)
    viewport_height: int = Field(default=720)
    timeout_ms: int = Field(default=30000, description="Default timeout in milliseconds")
    record_video: bool = Field(default=False, description="Record video of test execution")


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""

    enabled: bool = Field(default=False, description="Enable GitHub issue creation")
    token: str = Field(default="", description="GitHub token (or set GITHUB_TOKEN env var)")
    repo: str = Field(default="", description="Repository in owner/repo format")
    labels: list[str] = Field(
        default_factory=lambda: ["bug", "e2e-test-failure"],
        description="Labels for created issues",
    )
    assignees: list[str] = Field(default_factory=list, description="Default assignees")


class ReportConfig(BaseModel):
    """Report configuration."""

    output_dir: str = Field(default="reports", description="Report output directory")
    screenshots_dir: str = Field(default="screenshots", description="Screenshots directory")
    results_dir: str = Field(default="results", description="JSON results directory")
    html_report: bool = Field(default=True, description="Generate HTML report")
    json_report: bool = Field(default=True, description="Save JSON results")


class ForsetiConfig(BaseModel):
    """Root configuration for Forseti."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)

    @classmethod
    def from_env(cls) -> ForsetiConfig:
        """Create config from environment variables."""
        config = cls()

        # LLM
        if api_key := os.getenv("GEMINI_API_KEY"):
            config.llm.api_key = api_key
        if model := os.getenv("FORSETI_LLM_MODEL"):
            config.llm.model = model
        if provider := os.getenv("FORSETI_LLM_PROVIDER"):
            config.llm.provider = provider
        if base_url := os.getenv("FORSETI_LLM_BASE_URL"):
            config.llm.base_url = base_url

        # Browser
        if os.getenv("FORSETI_HEADED"):
            config.browser.headless = False

        # GitHub
        if token := os.getenv("GITHUB_TOKEN"):
            config.github.token = token
            config.github.enabled = True
        if repo := os.getenv("GITHUB_REPO"):
            config.github.repo = repo

        return config


# ── Multi-Project Config (Sprint 04) ────────────────────────────────


class AuthConfig(BaseModel):
    """Authentication configuration per project."""

    type: str = Field(default="none", description="Auth type: none, otp, bearer")
    email_env: str = Field(default="", description="Env var for admin email")
    password_env: str = Field(default="", description="Env var for admin password")
    token_env: str = Field(default="", description="Env var for bearer token")
    login_path: str = Field(default="/api/admin/login")
    verify_path: str = Field(default="/api/admin/verify-otp")


class ProjectConfig(BaseModel):
    """Configuration for a single test project."""

    base_url: str = Field(description="Target server base URL")
    test_script: str = Field(description="Path to YAML test script")
    auth: AuthConfig = Field(default_factory=AuthConfig)
    github_repo: str = Field(default="", description="GitHub repo (owner/name)")
    project_dir: str = Field(default="", description="Local path to project git repo for version detection")


def load_projects(yaml_path: str) -> dict[str, ProjectConfig]:
    """Load project configurations from forseti.yaml.

    Returns:
        Dict mapping project name → ProjectConfig.
    """
    import yaml

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    projects = {}
    for name, cfg in data.get("projects", {}).items():
        # Extract auth sub-config
        auth_data = cfg.pop("auth", {})
        auth = AuthConfig(**auth_data)

        # Extract github repo
        github_data = cfg.pop("github", {})
        github_repo = github_data.get("repo", "")

        projects[name] = ProjectConfig(
            base_url=cfg["base_url"],
            test_script=cfg["test_script"],
            auth=auth,
            github_repo=github_repo,
            project_dir=cfg.get("project_dir", ""),
        )

    return projects

