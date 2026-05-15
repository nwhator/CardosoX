"""Playwright deep crawler that renders pages and runs entity/quote extraction."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from extractors.entity_extractor import EntityExtractor
from quote_crawler.quote_extractor import QuoteExtractor
from quote_crawler.quote_matcher import QuoteMatcher

logger = logging.getLogger(__name__)


class DeepCrawler:
    def __init__(self, timeout_ms: int = 30000, retries: int = 3, default_region: str = "NG"):
        self.timeout_ms = timeout_ms
        self.retries = retries
        self.entity_extractor = EntityExtractor(default_region=default_region)
        self.quote_extractor = QuoteExtractor()
        self.quote_matcher = QuoteMatcher()

    async def crawl(self, browser: Any, url: str) -> dict:
        context = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page = await context.new_page()
        try:
            await page.route("**/*", self._block_heavy_resources)
            html = ""
            for attempt in range(self.retries):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    await self._settle_page(page)
                    html = await page.content()
                    break
                except Exception as exc:
                    if attempt == self.retries - 1:
                        raise
                    delay = 2**attempt
                    logger.info("Retrying %s after %ss: %s", url, delay, exc)
                    await asyncio.sleep(delay)

            companies = self.entity_extractor.extract(html, url)
            quotes = self.quote_extractor.extract(html, url)
            quotes = self.quote_matcher.match(quotes, companies)
            return {
                "source_url": url,
                "companies": companies,
                "quotes": quotes,
                "status": "success",
            }
        except Exception as exc:
            logger.exception("Deep crawl failed for %s", url)
            return {
                "source_url": url,
                "companies": [],
                "quotes": [],
                "status": "error",
                "error": str(exc),
            }
        finally:
            await context.close()

    async def _settle_page(self, page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 10000))
        except Exception:
            pass
        await page.evaluate(
            """
            async () => {
              const steps = 4;
              for (let i = 1; i <= steps; i++) {
                window.scrollTo(0, document.body.scrollHeight * i / steps);
                await new Promise(resolve => setTimeout(resolve, 250));
              }
              window.scrollTo(0, 0);
            }
            """
        )
        await page.wait_for_timeout(300)

    async def _block_heavy_resources(self, route) -> None:
        if route.request.resource_type in {"image", "font", "media"}:
            await route.abort()
            return
        await route.continue_()
