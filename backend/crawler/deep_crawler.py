"""Playwright deep crawler that renders pages and runs entity/quote extraction."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from crawler.discovery_crawler import DiscoveryCrawler
from extractors.entity_extractor import EntityExtractor
from quote_crawler.quote_extractor import QuoteExtractor
from quote_crawler.quote_matcher import QuoteMatcher

logger = logging.getLogger(__name__)


class DeepCrawler:
    def __init__(self, timeout_ms: int = 30000, retries: int = 3, default_region: str = "NG", ai_client: Any | None = None):
        self.timeout_ms = timeout_ms
        self.retries = retries
        self.default_region = default_region
        self.ai_client = ai_client
        self.entity_extractor = EntityExtractor(default_region=default_region, ai_client=ai_client)
        self.quote_extractor = QuoteExtractor()
        self.quote_matcher = QuoteMatcher()
        self.link_extractor = DiscoveryCrawler(timeout_ms=timeout_ms)

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

            entity_extractor = EntityExtractor(default_region=self.default_region, ai_client=self.ai_client)
            companies = await asyncio.to_thread(entity_extractor.extract, html, url)
            block_quotes = self.quote_extractor.extract_from_blocks(entity_extractor.last_blocks, url)
            page_quotes = self.quote_extractor.extract(html, url)
            ai_quotes = entity_extractor.last_ai_quotes
            quotes = [*block_quotes, *page_quotes, *ai_quotes]
            quotes = self.quote_matcher.match(quotes, companies)
            discovered_links = await asyncio.to_thread(self._rank_discovered_links, self.link_extractor.extract_internal_urls(html, url))
            return {
                "source_url": url,
                "companies": companies,
                "quotes": quotes,
                "discovered_links": discovered_links,
                "status": "success",
            }
        except Exception as exc:
            logger.exception("Deep crawl failed for %s", url)
            return {
                "source_url": url,
                "companies": [],
                "quotes": [],
                "discovered_links": [],
                "status": "error",
                "error": str(exc),
            }
        finally:
            await context.close()

    def _rank_discovered_links(self, links: list[str]) -> list[str]:
        if not links:
            return []
        local_scores = {link: self._local_page_score(link) for link in links}
        ai_scores = self.ai_client.score_pages(links) if self.ai_client else {}
        return sorted(
            links,
            key=lambda link: (max(local_scores.get(link, 0), ai_scores.get(link, 0)), -links.index(link)),
            reverse=True,
        )

    def _local_page_score(self, link: str) -> float:
        parsed = urlparse(link)
        text = f"{parsed.path} {parsed.query}".lower()
        score = 0.0
        priority = ("/contact", "/about", "/pricing", "/team", "/company", "/profile")
        if any(token in text for token in priority):
            score += 0.75
        if any(token in text for token in ("address", "location", "business", "vendor", "package", "quote", "fee", "cost")):
            score += 0.2
        return min(1.0, score)

    async def _settle_page(self, page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 10000))
        except Exception:
            pass
        await page.evaluate(
            """
            async () => {
              let lastHeight = 0;
              for (let i = 0; i < 8; i++) {
                const height = document.body.scrollHeight;
                window.scrollTo(0, height);
                await new Promise(resolve => setTimeout(resolve, 350));
                if (height === lastHeight) break;
                lastHeight = height;
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
