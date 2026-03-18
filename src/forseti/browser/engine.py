"""Ratatoskr-backed browser engine for Forseti.

Replaces direct Playwright usage with the shared Ratatoskr browser service.
Provides the same interface (start, stop, session, page operations)
but delegates browser ops to Ratatoskr HTTP API.

Migration: Playwright → Ratatoskr (/api/v1/scrape, /screenshot, /fetch)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx

from forseti.config import BrowserConfig

logger = logging.getLogger("forseti.browser.engine")

RATATOSKR_URL = os.getenv("RATATOSKR_URL", "http://ratatoskr:9200")


class RatatoskrPage:
    """Emulates a Playwright Page interface over Ratatoskr HTTP API.

    Provides goto(), screenshot(), title(), content(), evaluate() methods
    so existing ActionExecutor code continues to work with minimal changes.
    """

    def __init__(self, ratatoskr_url: str, timeout_ms: int = 30000):
        self.ratatoskr_url = ratatoskr_url
        self.timeout_ms = timeout_ms
        self.url = ""
        self._title = ""
        self._text = ""
        self._html = ""

    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int | None = None) -> None:
        """Navigate to a URL via Ratatoskr scrape API."""
        self.url = url
        async with httpx.AsyncClient(timeout=(timeout or self.timeout_ms) / 1000) as client:
            resp = await client.post(
                f"{self.ratatoskr_url}/api/v1/scrape",
                json={"url": url, "extract_text": True},
            )
            resp.raise_for_status()
            data = resp.json()
            self._title = data.get("title", "")
            self._text = data.get("text", "") or ""
            self._html = data.get("html", "") or ""

    async def title(self) -> str:
        return self._title

    async def content(self) -> str:
        return self._html

    async def screenshot(self, path: str | None = None, **kwargs) -> bytes | None:
        """Take a screenshot via Ratatoskr."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.ratatoskr_url}/api/v1/screenshot",
                json={"url": self.url},
            )
            resp.raise_for_status()
            if path:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, "wb") as f:
                    f.write(resp.content)
            return resp.content

    async def evaluate(self, expression: str) -> str:
        """Evaluate JS — returns cached text content (no live JS via API)."""
        if "innerText" in expression:
            return self._text[:2000]
        return ""

    def set_default_timeout(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms

    def locator(self, selector: str):
        """Return a Ratatoskr-compatible locator (limited functionality)."""
        return RatatoskrLocator(self, selector)

    def get_by_text(self, text: str):
        """Return a locator matching by text content."""
        return RatatoskrLocator(self, f"text={text}")

    async def wait_for_selector(self, selector: str, timeout: int | None = None) -> None:
        """Check if selector text exists in page content."""
        if selector.startswith("text="):
            target = selector[5:].strip("'\"")
            if target.lower() not in self._text.lower():
                raise AssertionError(f"Text '{target}' not found on page")


class RatatoskrLocator:
    """Minimal locator — text assertions only via scraped content."""

    def __init__(self, page: RatatoskrPage, selector: str):
        self._page = page
        self._selector = selector

    async def click(self, timeout: int | None = None) -> None:
        """Click element via Ratatoskr /api/v1/interact."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._page.ratatoskr_url}/api/v1/interact",
                json={"url": self._page.url, "actions": [{"type": "click", "selector": self._selector}]},
            )
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(f"click failed: {data['error']}")
            # Refresh page state
            self._page._title = data.get("title", self._page._title)

    async def fill(self, value: str, timeout: int | None = None) -> None:
        """Fill input via Ratatoskr /api/v1/interact."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._page.ratatoskr_url}/api/v1/interact",
                json={"url": self._page.url, "actions": [{"type": "fill", "selector": self._selector, "value": value}]},
            )
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(f"fill failed: {data['error']}")

    async def select_option(self, value: str, timeout: int | None = None) -> None:
        """Select dropdown via Ratatoskr /api/v1/interact."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._page.ratatoskr_url}/api/v1/interact",
                json={"url": self._page.url, "actions": [{"type": "select", "selector": self._selector, "value": value}]},
            )
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(f"select failed: {data['error']}")

    async def hover(self, timeout: int | None = None) -> None:
        logger.warning(f"hover('{self._selector}') — not supported via Ratatoskr API")

    async def wait_for(self, timeout: int | None = None) -> None:
        """Check text exists on page."""
        text = self._selector.replace("text=", "").strip("'\"")
        if text.lower() not in self._page._text.lower():
            raise AssertionError(f"Text '{text}' not found on page")

    def or_(self, *others):
        return self


class BrowserEngine:
    """Manages browser operations via Ratatoskr shared service.

    Drop-in replacement for the Playwright-based BrowserEngine.
    """

    def __init__(self, config: BrowserConfig):
        self.config = config
        self.ratatoskr_url = RATATOSKR_URL

    async def start(self) -> None:
        """Verify Ratatoskr is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.ratatoskr_url}/healthz")
                resp.raise_for_status()
            logger.info(f"🌐 Connected to Ratatoskr at {self.ratatoskr_url}")
        except Exception as e:
            logger.warning(f"⚠️ Ratatoskr not available at {self.ratatoskr_url}: {e}")

    async def stop(self) -> None:
        """No-op — Ratatoskr manages its own browser lifecycle."""
        logger.info("🌐 Ratatoskr session closed (no-op)")

    async def new_context(self, video_dir: Path | None = None):
        """Return a simple context (no-op with Ratatoskr)."""
        return RatatoskrContext(self.ratatoskr_url, self.config)

    async def new_page(self, context) -> RatatoskrPage:
        """Create a new Ratatoskr page wrapper."""
        page = RatatoskrPage(self.ratatoskr_url, self.config.timeout_ms)
        return page

    @asynccontextmanager
    async def session(self, video_dir: Path | None = None):
        """Context manager for a browser session.

        Usage:
            async with engine.session() as page:
                await page.goto("https://example.com")
        """
        page = RatatoskrPage(self.ratatoskr_url, self.config.timeout_ms)
        try:
            yield page
        finally:
            pass  # No cleanup needed — Ratatoskr manages browser


class RatatoskrContext:
    """Minimal context that mimics Playwright BrowserContext."""

    def __init__(self, ratatoskr_url: str, config: BrowserConfig):
        self.ratatoskr_url = ratatoskr_url
        self.config = config

    async def close(self) -> None:
        pass  # No-op
