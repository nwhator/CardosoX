"""Production entity-aware crawler facade used by the Flask API."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import requests

from ai.groq_client import GroqClient
from crawler.deep_crawler import DeepCrawler
from crawler.discovery_crawler import DiscoveryCrawler
from crawler.queue_manager import QueueManager
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter
from extractors.entity_extractor import EntityExtractor
from matchers.entity_matcher import EntityMatcher
from utils.cleaners import unique_keep_order

logger = logging.getLogger(__name__)

try:
    import cloudscraper
except Exception:  # pragma: no cover - optional production dependency
    cloudscraper = None


class WebScraper:
    """Entity-aware intelligence crawler with quote extraction.

    Public methods intentionally preserve the previous synchronous API used by
    app.py while the implementation runs an async Playwright worker pipeline.
    """

    def __init__(self):
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        playwright_timeout_ms = int(os.getenv("PLAYWRIGHT_TIMEOUT", str(int(os.getenv("SCRAPER_TIMEOUT", "30")) * 1000)))
        self.timeout = max(1, playwright_timeout_ms // 1000)
        self.concurrency = int(os.getenv("MAX_CONCURRENT_PAGES", os.getenv("SCRAPER_WORKERS", "5")))
        self.max_discovery_links = int(os.getenv("MAX_DISCOVERY_LINKS", os.getenv("MAX_CRAWL_PAGES", "150")))
        self.max_crawl_pages = int(os.getenv("MAX_CRAWL_PAGES", str(self.max_discovery_links)))
        self.crawl_depth = int(os.getenv("MAX_CRAWL_DEPTH", os.getenv("CRAWL_DEPTH", "3")))
        self.default_region = os.getenv("PHONE_DEFAULT_REGION", "NG")
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./exports"))
        self.partial_save_dir = os.getenv("PARTIAL_SAVE_DIR", str(self.output_dir / "partials")).strip()
        self.csv_export_enabled = os.getenv("CSV_EXPORT", "true").lower() == "true"
        self.json_export_enabled = os.getenv("JSON_EXPORT", "true").lower() == "true"

        self.cs = cloudscraper.create_scraper() if cloudscraper else requests.Session()
        # Ensure non-cloudscraper sessions present a realistic browser User-Agent
        try:
            default_headers = {
                "User-Agent": os.getenv(
                    "SCRAPER_USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            if hasattr(self.cs, "headers") and isinstance(self.cs.headers, dict):
                # merge without overwriting any existing configured headers
                for k, v in default_headers.items():
                    self.cs.headers.setdefault(k, v)
        except Exception:
            pass
        self.ai_client = GroqClient()
        self.discovery = DiscoveryCrawler(
            timeout_ms=self.timeout * 1000,
            max_links_per_seed=self.max_discovery_links,
        )
        self.deep = DeepCrawler(
            timeout_ms=self.timeout * 1000,
            retries=self.max_retries,
            default_region=self.default_region,
            ai_client=self.ai_client,
        )
        self.entity_matcher = EntityMatcher()
        self.csv_exporter = CsvExporter()
        self.json_exporter = JsonExporter()

    def scrape_multiple_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        try:
            return asyncio.run(self._crawl_many(urls))
        except RuntimeError as exc:
            if "asyncio.run() cannot be called" in str(exc):
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(self._crawl_many(urls))
                except Exception as loop_exc:
                    logger.exception("Async crawler failed inside existing event loop; falling back: %s", loop_exc)
                    return [self._scrape_with_cloudscraper(url) for url in urls]
                finally:
                    loop.close()
            logger.exception("Async crawler failed; falling back to cloudscraper/requests: %s", exc)
            return [self._scrape_with_cloudscraper(url) for url in urls]
        except Exception as exc:
            logger.exception("Async crawler failed; falling back to cloudscraper/requests: %s", exc)
            return [self._scrape_with_cloudscraper(url) for url in urls]

    def scrape_url(self, url: str) -> dict[str, Any]:
        return self.scrape_multiple_urls([url])[0]

    def export_csv(self, results: list[dict[str, Any]], path: str | Path | None = None) -> str:
        csv_text = self.csv_exporter.dumps(results)
        if path:
            self.csv_exporter.save(results, path)
        return csv_text

    def export_json(self, results: list[dict[str, Any]], path: str | Path | None = None) -> str:
        json_text = self.json_exporter.dumps(results)
        if path:
            self.json_exporter.save(results, path)
        return json_text

    async def _crawl_many(self, urls: list[str]) -> list[dict[str, Any]]:
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            raise RuntimeError("Playwright is required for rendered crawling. Install requirements and run `playwright install chromium`.") from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            try:
                tasks = [self._crawl_seed(browser, url) for url in urls]
                return await asyncio.gather(*tasks)
            finally:
                await browser.close()

    async def _crawl_seed(self, browser: Any, seed_url: str) -> dict[str, Any]:
        discovered_urls = await self.discovery.discover(browser, seed_url)
        discovered_urls = await asyncio.to_thread(self.deep._rank_discovered_links, discovered_urls)
        queue = QueueManager()
        for url in discovered_urls:
            if len(queue.visited) >= self.max_crawl_pages:
                break
            await queue.add(url, depth=0)

        page_results: list[dict[str, Any]] = []

        async def worker() -> None:
            while True:
                job = await queue.get()
                try:
                    result = await self.deep.crawl(browser, job.url)
                    page_results.append(result)
                    if job.depth < self.crawl_depth:
                        for link in result.get("discovered_links", []):
                            if len(queue.visited) >= self.max_crawl_pages:
                                break
                            await queue.add(link, depth=job.depth + 1)
                    self._save_partial(seed_url, page_results)
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(max(1, self.concurrency))]
        await queue.join()
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        result = self._aggregate_seed_result(seed_url, discovered_urls, page_results)
        self._save_exports(seed_url, result)
        return result

    def _aggregate_seed_result(self, seed_url: str, discovered_urls: list[str], page_results: list[dict[str, Any]]) -> dict[str, Any]:
        companies = []
        quotes = []
        errors = []
        for result in page_results:
            companies.extend(result.get("companies", []))
            quotes.extend(result.get("quotes", []))
            if result.get("status") == "error":
                errors.append({"source_url": result.get("source_url"), "error": result.get("error")})

        companies = self.entity_matcher.merge_entities(companies)
        quotes = self._dedupe_quotes(quotes)
        for company in companies:
            if company.get("confidence", 0) < 0.45:
                logger.info("Low-confidence company retained: %s source=%s", company.get("company_name"), company.get("source_url"))

        result = {
            "source_url": seed_url,
            "discovered_urls": discovered_urls,
            "crawled_urls": [result.get("source_url") for result in page_results if result.get("source_url")],
            "companies": companies,
            "quotes": quotes,
            "status": "partial" if errors and (companies or quotes) else "error" if errors else "success",
            "errors": errors,
        }
        self._add_legacy_fields(result)
        return result

    def _add_legacy_fields(self, result: dict[str, Any]) -> None:
        primary = result.get("companies", [{}])[0] if result.get("companies") else {}
        result["url"] = result.get("source_url")
        result["company_name"] = primary.get("company_name")
        result["emails"] = unique_keep_order(
            email for company in result.get("companies", []) for email in company.get("emails", [])
        )
        result["phone_numbers"] = unique_keep_order(
            phone for company in result.get("companies", []) for phone in company.get("phone_numbers", [])
        )
        result["phones"] = result["phone_numbers"]
        result["addresses"] = unique_keep_order(
            address for company in result.get("companies", []) for address in company.get("addresses", [])
        )

    def _dedupe_quotes(self, quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        seen: set[str] = set()
        for quote in sorted(quotes, key=lambda item: item.get("confidence", 0), reverse=True):
            key = "|".join(
                [
                    str(quote.get("company", "")).lower(),
                    str(quote.get("title", "")).lower(),
                    str(quote.get("price", "")).lower(),
                    str(quote.get("source_url", "")).lower(),
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            output.append(quote)
        return output

    def _save_partial(self, seed_url: str, page_results: list[dict[str, Any]]) -> None:
        if not self.partial_save_dir or not page_results:
            return
        try:
            safe_name = "".join(ch if ch.isalnum() else "_" for ch in seed_url)[:120]
            path = Path(self.partial_save_dir) / f"{safe_name}.partial.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.json_exporter.save(page_results, path)
        except Exception as exc:
            logger.debug("Partial save failed for %s: %s", seed_url, exc)

    def _save_exports(self, seed_url: str, result: dict[str, Any]) -> None:
        if not self.csv_export_enabled and not self.json_export_enabled:
            return
        try:
            safe_name = "".join(ch if ch.isalnum() else "_" for ch in seed_url)[:120]
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if self.json_export_enabled:
                self.json_exporter.save([result], self.output_dir / f"{safe_name}.json")
            if self.csv_export_enabled:
                self.csv_exporter.save([result], self.output_dir / f"{safe_name}.csv")
        except Exception as exc:
            logger.debug("Export save failed for %s: %s", seed_url, exc)

    def _scrape_with_cloudscraper(self, url: str) -> dict[str, Any]:
        try:
            response = self.cs.get(url, timeout=self.timeout)
            response.raise_for_status()
            entity_extractor = EntityExtractor(default_region=self.default_region, ai_client=self.ai_client)
            companies = entity_extractor.extract(response.text, url)
            quotes = [
                *self.deep.quote_extractor.extract_from_blocks(entity_extractor.last_blocks, url),
                *self.deep.quote_extractor.extract(response.text, url),
                *entity_extractor.last_ai_quotes,
            ]
            quotes = self.deep.quote_matcher.match(quotes, companies)
            result = {
                "source_url": url,
                "discovered_urls": [url],
                "companies": companies,
                "quotes": quotes,
                "status": "success",
                "errors": [],
            }
            self._add_legacy_fields(result)
            return result
        except Exception as exc:
            logger.exception("Cloudscraper fallback failed for %s", url)
            return {
                "source_url": url,
                "url": url,
                "companies": [],
                "quotes": [],
                "company_name": None,
                "emails": [],
                "phone_numbers": [],
                "addresses": [],
                "status": "error",
                "errors": [{"source_url": url, "error": str(exc)}],
            }
