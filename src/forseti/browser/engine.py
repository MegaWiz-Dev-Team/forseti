"""Playwright browser engine for Forseti."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from forseti.config import BrowserConfig

logger = logging.getLogger("forseti.browser.engine")


class BrowserEngine:
    """Manages Playwright browser lifecycle."""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        """Launch the browser."""
        pw = await async_playwright().start()
        self._playwright = pw

        browser_type = getattr(pw, self.config.browser_type, pw.chromium)
        self._browser = await browser_type.launch(headless=self.config.headless)
        logger.info(
            f"🌐 Browser launched: {self.config.browser_type} "
            f"(headless={self.config.headless})"
        )

    async def stop(self) -> None:
        """Close the browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("🌐 Browser closed")

    async def new_context(self, video_dir: Path | None = None) -> BrowserContext:
        """Create a new browser context with configured viewport."""
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")

        context_opts: dict = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
        }

        if self.config.record_video and video_dir:
            video_dir.mkdir(parents=True, exist_ok=True)
            context_opts["record_video_dir"] = str(video_dir)
            context_opts["record_video_size"] = {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            }

        return await self._browser.new_context(**context_opts)

    async def new_page(self, context: BrowserContext) -> Page:
        """Create a new page in the given context."""
        page = await context.new_page()
        page.set_default_timeout(self.config.timeout_ms)
        return page

    @asynccontextmanager
    async def session(self, video_dir: Path | None = None):
        """Context manager for a full browser session (context + page).

        Usage:
            async with engine.session() as page:
                await page.goto("https://example.com")
        """
        context = await self.new_context(video_dir)
        page = await self.new_page(context)
        try:
            yield page
        finally:
            await context.close()
