#!/usr/bin/env python3
"""Selenium browser automation with optimized defaults and offloading."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from browser_automation.supermemory_offloader import offloader


class SeleniumAutomation:
    """Selenium WebDriver with aggressive startup optimization and offloading."""

    def __init__(
        self,
        headless: bool = True,
        wait_timeout: int = 10,
        page_load_timeout: int = 30,
        window_size: str = "1920,1080",
    ) -> None:
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.page_load_timeout = page_load_timeout
        self.window_size = window_size
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self._init_lock = asyncio.Lock()
        self._driver_lock = asyncio.Lock()

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument(f"--window-size={self.window_size}")
        options.page_load_strategy = "eager"

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver

    async def initialize(self) -> None:
        """Initialize Selenium WebDriver lazily with thread offload to avoid blocking."""

        if self.driver:
            return

        async with self._init_lock:
            if self.driver:
                return
            driver = await asyncio.to_thread(self._create_driver)
            self.driver = driver
            self.wait = WebDriverWait(driver, self.wait_timeout)

    def _scrape_sync(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        assert self.driver is not None  # guarded by initialize
        assert self.wait is not None

        self.driver.get(url)

        data: Dict[str, Any] = {}
        for key, selector in selectors.items():
            try:
                element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                data[key] = element.text
            except Exception as exc:  # noqa: BLE001 - Selenium raises many types
                data[key] = f"Error: {exc}"

        return data

    async def scrape_with_offload(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Scrape CSS selectors with immediate offload of results."""

        if not self.driver:
            await self.initialize()

        async with self._driver_lock:
            data = await asyncio.to_thread(self._scrape_sync, url, selectors)

        cloud_ref = await offloader.offload_immediately(
            {
                "url": url,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "type": "selenium_scrape",
            }
        )

        return {"cloud_ref": cloud_ref["ref_id"]}

    def close(self) -> None:
        """Cleanup Selenium resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None


async def example_usage():
    """Example: Scrape with context offloading"""

    automation = SeleniumAutomation(headless=True)
    await automation.initialize()

    # Scrape with offload
    result = await automation.scrape_with_offload(
        'https://example.com',
        {'title': 'h1', 'content': '.content'}
    )

    print(f"Result: {result}")
    print(f"Local memory footprint: {len(str(result))} chars")

    automation.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
