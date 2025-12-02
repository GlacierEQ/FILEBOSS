#!/usr/bin/env python3
"""Playwright browser automation with optimized resource reuse and offloading."""

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from browser_automation.supermemory_offloader import offloader


class PlaywrightAutomation:
    """High-throughput Playwright automation with resilient navigation.

    Key optimizations:
    * Single reusable context to avoid repeated profile creation.
    * Concurrency throttling via semaphore to protect system resources.
    * Navigation retries with incremental backoff to smooth transient errors.
    * Immediate offload to Supermemory to keep local footprint minimal.
    """

    def __init__(
        self,
        *,
        browser_type: str = "chromium",
        headless: bool = True,
        max_concurrent_pages: int = 4,
        viewport: Optional[Mapping[str, int]] = None,
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        navigation_timeout_ms: int = 30_000,
        navigation_retries: int = 2,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        self.browser_type = browser_type
        self.headless = headless
        self.max_concurrent_pages = max_concurrent_pages
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.user_agent = user_agent
        self.navigation_timeout_ms = navigation_timeout_ms
        self.navigation_retries = navigation_retries
        self.retry_backoff_seconds = retry_backoff_seconds

        self.browser: Optional[Browser] = None
        self.playwright = None
        self._context: Optional[BrowserContext] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_pages)

    async def initialize(self, headless: Optional[bool] = None) -> None:
        """Start Playwright and create a shared browser context."""

        if self.browser:
            return

        self.playwright = await async_playwright().start()

        browser_factory = getattr(self.playwright, self.browser_type, None)
        if browser_factory is None:
            raise ValueError(
                f"Unsupported browser type '{self.browser_type}'. "
                "Use 'chromium', 'firefox', or 'webkit'."
            )

        self.browser = await browser_factory.launch(
            headless=self.headless if headless is None else headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        self._context = await self.browser.new_context(
            viewport=dict(self.viewport),
            user_agent=self.user_agent,
            java_script_enabled=True,
        )

    async def _ensure_initialized(self) -> None:
        if not self.browser or not self._context:
            await self.initialize()

    async def __aenter__(self) -> "PlaywrightAutomation":
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _offload_or_return(
        self, action_name: str, action_result: Any, url: str
    ) -> Any:
        cloud_ref = await offloader.offload_immediately(
            {
                "action": action_name,
                "result": action_result,
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "type": "playwright_action",
            }
        )
        return cloud_ref["ref_id"]

    async def _navigate_with_retry(self, page: Page, url: str) -> None:
        last_error: Optional[Exception] = None
        for attempt in range(self.navigation_retries + 1):
            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.navigation_timeout_ms,
                )
                return
            except Exception as exc:  # noqa: BLE001 - intentional broad retry
                last_error = exc
                if attempt < self.navigation_retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (attempt + 1))
                else:
                    raise last_error

    async def scrape_with_offload(
        self,
        url: str,
        actions: Mapping[str, Callable[[Page], Awaitable[Any]]],
    ) -> Dict[str, Any]:
        """Execute actions on a page with retries and immediate offloading."""

        await self._ensure_initialized()

        async with self._semaphore:
            page = await self._context.new_page()
            try:
                await self._navigate_with_retry(page, url)

                results: Dict[str, Any] = {}
                for action_name, action_func in actions.items():
                    action_result = await action_func(page)
                    results[action_name] = await self._offload_or_return(
                        action_name, action_result, url
                    )

                return results
            finally:
                await page.close()

    async def batch_scrape(
        self, urls: Iterable[str], action: Callable[[Page], Awaitable[Any]]
    ) -> List[Any]:
        """Scrape multiple URLs concurrently with connection reuse."""

        tasks = [self.scrape_with_offload(url, {"extract": action}) for url in urls]
        results = await asyncio.gather(*tasks)
        return [result["extract"] for result in results]

    async def close(self) -> None:
        """Cleanup resources and prevent dangling Playwright processes."""

        if self._context:
            await self._context.close()
            self._context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None


async def example_usage():
    """Example: Extract titles from multiple pages"""
    
    automation = PlaywrightAutomation()
    await automation.initialize()
    
    # Define extraction action
    async def extract_title(page: Page) -> str:
        return await page.title()
    
    # Scrape with auto-offload
    urls = ['https://example.com', 'https://github.com']
    
    cloud_refs = await automation.batch_scrape(urls, extract_title)
    
    print(f"Scraped {len(urls)} pages")
    print(f"Cloud references: {cloud_refs}")
    print(f"Local memory footprint: {len(str(cloud_refs))} chars (minimal!)")
    
    await automation.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
