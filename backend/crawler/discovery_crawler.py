"""Discovery crawler that collects only likely company/profile/contact URLs."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.cleaners import looks_like_asset, normalize_url, unique_keep_order

logger = logging.getLogger(__name__)


DISCOVERY_KEYWORDS = (
    "company",
    "companies",
    "profile",
    "business",
    "vendor",
    "listing",
    "directory",
    "about",
    "contact",
    "pricing",
    "packages",
    "services",
)


class DiscoveryCrawler:
    def __init__(self, timeout_ms: int = 30000, max_links_per_seed: int = 40):
        self.timeout_ms = timeout_ms
        self.max_links_per_seed = max_links_per_seed

    async def discover(self, browser: Any, seed_url: str) -> list[str]:
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.route("**/*", self._block_heavy_resources)
            await page.goto(seed_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            html = await page.content()
            urls = self.extract_company_urls(html, seed_url)
            return unique_keep_order([seed_url, *urls])[: self.max_links_per_seed]
        except Exception as exc:
            logger.warning("Discovery failed for %s: %s", seed_url, exc)
            return [seed_url]
        finally:
            await context.close()

    async def _block_heavy_resources(self, route) -> None:
        if route.request.resource_type in {"image", "font", "media"}:
            await route.abort()
            return
        await route.continue_()

    def extract_company_urls(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        base_domain = urlparse(base_url).netloc.lower().removeprefix("www.")
        urls: list[str] = []
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            url = normalize_url(href, base_url)
            if not url or looks_like_asset(url):
                continue
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            if domain and domain != base_domain:
                continue
            text = f"{link.get_text(' ')} {parsed.path}".lower()
            if any(keyword in text for keyword in DISCOVERY_KEYWORDS):
                urls.append(url)
        return unique_keep_order(urls)
