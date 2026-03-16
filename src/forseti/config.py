"""Configuration management for Forseti."""

from __future__ import annotations

import os
from pathlib import Path

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
