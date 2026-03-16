"""Tests for Forseti configuration."""

import os
import pytest

from forseti.config import ForsetiConfig, LLMConfig, BrowserConfig, GitHubConfig


class TestLLMConfig:
    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "gemini"
        assert config.model == "gemini-2.0-flash"
        assert config.temperature == 0.1

    def test_custom_values(self):
        config = LLMConfig(provider="ollama", model="llama3", base_url="http://localhost:11434/v1")
        assert config.provider == "ollama"
        assert config.base_url == "http://localhost:11434/v1"


class TestBrowserConfig:
    def test_defaults(self):
        config = BrowserConfig()
        assert config.headless is True
        assert config.browser_type == "chromium"
        assert config.viewport_width == 1280

    def test_headed_mode(self):
        config = BrowserConfig(headless=False)
        assert config.headless is False


class TestGitHubConfig:
    def test_defaults(self):
        config = GitHubConfig()
        assert config.enabled is False
        assert config.labels == ["bug", "e2e-test-failure"]

    def test_enabled(self):
        config = GitHubConfig(enabled=True, token="tok", repo="owner/repo")
        assert config.enabled is True
        assert config.repo == "owner/repo"


class TestForsetiConfig:
    def test_from_env_gemini_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        config = ForsetiConfig.from_env()
        assert config.llm.api_key == "test-key-123"

    def test_from_env_github(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "gh-token")
        monkeypatch.setenv("GITHUB_REPO", "user/repo")
        config = ForsetiConfig.from_env()
        assert config.github.enabled is True
        assert config.github.token == "gh-token"
        assert config.github.repo == "user/repo"

    def test_from_env_headed(self, monkeypatch):
        monkeypatch.setenv("FORSETI_HEADED", "1")
        config = ForsetiConfig.from_env()
        assert config.browser.headless is False

    def test_from_env_custom_llm(self, monkeypatch):
        monkeypatch.setenv("FORSETI_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("FORSETI_LLM_MODEL", "llama3")
        monkeypatch.setenv("FORSETI_LLM_BASE_URL", "http://localhost:11434/v1")
        config = ForsetiConfig.from_env()
        assert config.llm.provider == "ollama"
        assert config.llm.model == "llama3"
