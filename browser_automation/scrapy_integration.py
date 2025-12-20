#!/usr/bin/env python3
"""
Scrapy + Playwright Integration
High-performance crawling with memory offloading
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_playwright.page import PageMethod
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from browser_automation.supermemory_offloader import offloader
except ImportError:
    offloader = None


class SmartSpider(scrapy.Spider):
    """Scrapy spider with Playwright and memory offloading"""
    
    name = 'smart_spider'
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage']
        },
    }
    
    def __init__(self, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls or ['https://example.com']
    
    def start_requests(self):
        """Initialize crawl with Playwright"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'body'),
                    ],
                },
                callback=self.parse_with_offload
            )
    
    def parse_with_offload(self, response):
        """Parse and immediately offload to cloud"""
        
        data = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'h1': response.css('h1::text').get(),
            'links': response.css('a::attr(href)').getall()[:10],
        }
        
        # Offload to cloud
        if offloader:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cloud_ref = loop.run_until_complete(
                offloader.offload_immediately(data)
            )
            loop.close()
            
            yield {'cloud_ref': cloud_ref['ref_id'], 'url': response.url}
        else:
            yield data


def run_spider(urls: List[str]):
    """Run spider with context offloading"""
    
    process = CrawlerProcess(settings={
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'results.json': {'format': 'json'},
        }
    })
    
    process.crawl(SmartSpider, urls=urls)
    process.start()


if __name__ == "__main__":
    test_urls = [
        'https://example.com',
        'https://github.com'
    ]
    run_spider(test_urls)
