"""Pricing, quote, package, and fee extraction."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from utils.cleaners import clean_text, unique_keep_order
from utils.scoring import quote_confidence


CURRENCY_MAP = {
    "\u20a6": "NGN",
    "$": "USD",
    "\u00a3": "GBP",
    "\u20ac": "EUR",
    "NGN": "NGN",
    "N": "NGN",
    "USD": "USD",
    "GBP": "GBP",
}
PRICE_RE = re.compile(r"(?P<currency>NGN|USD|GBP|N|\u20a6|\$|\u00a3|\u20ac)\s?(?P<amount>\d[\d,]*(?:\.\d{1,2})?)", re.I)
STARTING_RE = re.compile(r"\b(starting from|starts at|from|as low as|packages? from|fees?)\b", re.I)
QUOTE_CONTAINER_SELECTORS = [
    ".pricing",
    ".price",
    ".plan",
    ".package",
    ".fee",
    ".quote",
    "[class*='pricing']",
    "[class*='package']",
    "[class*='price']",
    "table",
    "article",
    "section",
    "li",
]


class QuoteExtractor:
    def extract(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        containers = self._find_quote_containers(soup)
        quotes: list[dict] = []
        for container in containers:
            quote = self._extract_from_container(container, source_url)
            if quote:
                quotes.append(quote)
        return self._dedupe(quotes)

    def _find_quote_containers(self, soup: BeautifulSoup) -> list[Tag]:
        page_text_len = len(clean_text(soup.get_text(" ")))
        containers: list[Tag] = []
        for selector in QUOTE_CONTAINER_SELECTORS:
            for node in soup.select(selector):
                text = clean_text(node.get_text(" "))
                if len(text) < 8 or not PRICE_RE.search(text):
                    continue
                if page_text_len and len(text) / page_text_len > 0.75:
                    continue
                containers.append(node)
        if not containers and PRICE_RE.search(clean_text(soup.get_text(" "))):
            containers.append(soup.body or soup)
        return self._dedupe_nodes(containers)[:80]

    def _extract_from_container(self, node: Tag, source_url: str) -> dict | None:
        text = clean_text(node.get_text(" "), 600)
        match = PRICE_RE.search(text)
        if not match:
            return None
        currency_token = match.group("currency")
        currency = CURRENCY_MAP.get(currency_token.upper(), CURRENCY_MAP.get(currency_token, currency_token.upper()))
        price = f"{currency_token}{match.group('amount')}"
        title = self._extract_title(node, text)
        quote = {
            "company": "",
            "title": title,
            "price": price,
            "currency": currency,
            "description": self._extract_description(text, title, price),
            "source_url": source_url,
            "confidence": 0.0,
        }
        quote["confidence"] = quote_confidence(
            quote,
            {
                "pricing_container": True,
                "starting_from": bool(STARTING_RE.search(text)),
            },
        )
        return quote

    def _extract_title(self, node: Tag, text: str) -> str:
        for selector in ("h1", "h2", "h3", "h4", ".title", ".plan-name", ".package-name"):
            item = node.select_one(selector)
            if item:
                title = clean_text(item.get_text(" "), 120)
                if title:
                    return title
        before_price = PRICE_RE.split(text, maxsplit=1)[0]
        return clean_text(before_price, 80) or "Pricing"

    def _extract_description(self, text: str, title: str, price: str) -> str:
        description = text.replace(title, "", 1).replace(price, "", 1)
        return clean_text(description, 300)

    def _dedupe_nodes(self, nodes: list[Tag]) -> list[Tag]:
        output: list[Tag] = []
        for node in nodes:
            if any(existing in node.parents for existing in output):
                continue
            output = [existing for existing in output if node not in existing.parents]
            output.append(node)
        return output

    def _dedupe(self, quotes: list[dict]) -> list[dict]:
        keys = unique_keep_order([f"{quote.get('title')}|{quote.get('price')}|{quote.get('description')}" for quote in quotes])
        output: list[dict] = []
        for key in keys:
            title, price, description = key.split("|", 2)
            match = next(
                quote
                for quote in quotes
                if quote.get("title") == title and quote.get("price") == price and quote.get("description") == description
            )
            output.append(match)
        return output

