"""Discovery crawler for same-domain listing/detail/contact/pricing URLs."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.cleaners import clean_text, looks_like_asset, normalize_url, unique_keep_order

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
    "detail",
    "details",
    "shop",
    "store",
    "branch",
    "location",
    "locations",
    "page",
)
SKIP_KEYWORDS = (
    "login",
    "signin",
    "sign-in",
    "register",
    "cart",
    "checkout",
    "privacy",
    "terms",
    "cookie",
    "logout",
    "account",
    "wp-admin",
    "feed",
    "rss",
)
PAGINATION_RE = ("page=", "/page/", "paged=", "pagenum=", "offset=")


class DiscoveryCrawler:
    def __init__(self, timeout_ms: int = 30000, max_links_per_seed: int = 150, include_all_internal: bool = True):
        self.timeout_ms = timeout_ms
        self.max_links_per_seed = max_links_per_seed
        self.include_all_internal = include_all_internal

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
        return self.extract_internal_urls(html, base_url, include_all_internal=self.include_all_internal)

    def extract_internal_urls(self, html: str, base_url: str, include_all_internal: bool = True) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        base_domain = urlparse(base_url).netloc.lower().removeprefix("www.")
        scored_urls: list[tuple[int, str]] = []
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            url = normalize_url(href, base_url)
            if not url or looks_like_asset(url) or self._should_skip_url(url):
                continue
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            if domain and domain != base_domain:
                continue
            score = self._score_link(link, url)
            if score > 0 or include_all_internal:
                scored_urls.append((score, url))

        ranked = [url for _score, url in sorted(scored_urls, key=lambda item: item[0], reverse=True)]
        return unique_keep_order(ranked)[: self.max_links_per_seed]

    def _score_link(self, link, url: str) -> int:
        parsed = urlparse(url)
        text = f"{clean_text(link.get_text(' '))} {parsed.path} {parsed.query}".lower()
        score = 0
        if any(keyword in text for keyword in DISCOVERY_KEYWORDS):
            score += 20
        if any(token in text for token in PAGINATION_RE):
            score += 18
        if re_match_listing_id(parsed.path):
            score += 12
        if clean_text(link.get_text(" ")):
            score += 3
        return score

    def _should_skip_url(self, url: str) -> bool:
        parsed = urlparse(url)
        combined = f"{parsed.path}?{parsed.query}".lower()
        return any(keyword in combined for keyword in SKIP_KEYWORDS)


def re_match_listing_id(path: str) -> bool:
    parts = [part for part in path.strip("/").split("/") if part]
    if len(parts) >= 2 and any(char.isdigit() for char in parts[-1]):
        return True
    return len(parts) >= 2 and "-" in parts[-1] and len(parts[-1]) >= 8
