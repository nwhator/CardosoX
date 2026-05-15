"""Entity-aware extraction from company cards, blocks, and rendered pages."""

from __future__ import annotations

import json
import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from extractors.address_extractor import AddressExtractor
from extractors.email_extractor import EmailExtractor
from extractors.phone_extractor import PhoneExtractor
from matchers.entity_matcher import EntityMatcher
from utils.cleaners import clean_company_name, clean_text, domain_from_url, normalize_url, unique_keep_order
from utils.scoring import entity_confidence
from utils.validators import has_real_entity_name

logger = logging.getLogger(__name__)


SOCIAL_DOMAINS = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com", "tiktok.com")
COMPANY_BLOCK_SELECTORS = [
    "[itemscope][itemtype*='Organization']",
    "[itemscope][itemtype*='LocalBusiness']",
    ".company-card",
    ".company",
    ".profile-card",
    ".business-card",
    ".vendor-card",
    ".listing",
    ".directory-item",
    "article",
    "li",
    "section",
]


class EntityExtractor:
    def __init__(self, default_region: str = "NG"):
        self.email_extractor = EmailExtractor()
        self.phone_extractor = PhoneExtractor(default_region=default_region)
        self.address_extractor = AddressExtractor()
        self.matcher = EntityMatcher()

    def extract(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        blocks = self.detect_company_blocks(soup)
        if not blocks:
            blocks = [soup.body or soup]

        entities: list[dict] = []
        for block in blocks:
            entity = self._extract_from_block(block, source_url, fallback_page=block is (soup.body or soup))
            if self._is_useful_entity(entity):
                entities.append(entity)

        entities.extend(self._extract_structured_data(soup, source_url))
        merged = self.matcher.merge_entities(entities)
        low_confidence = [item for item in merged if item.get("confidence", 0) < 0.45]
        for entity in low_confidence:
            logger.info("Low confidence entity match: %s source=%s", entity.get("company_name"), source_url)
        return merged

    def detect_company_blocks(self, soup: BeautifulSoup) -> list[Tag]:
        candidates: list[Tag] = []
        page_text_len = len(clean_text(soup.get_text(" ")))
        for selector in COMPANY_BLOCK_SELECTORS:
            for node in soup.select(selector):
                if not isinstance(node, Tag):
                    continue
                text = clean_text(node.get_text(" "))
                if len(text) < 20:
                    continue
                if page_text_len and len(text) / page_text_len > 0.75:
                    continue
                signals = self._block_signal_count(node)
                if signals >= 2 or (signals >= 1 and self._extract_name(node)):
                    candidates.append(node)
        return self._dedupe_nested_blocks(candidates)

    def _block_signal_count(self, node: Tag) -> int:
        signals = 0
        if self._extract_name(node):
            signals += 1
        if self.email_extractor.extract(node):
            signals += 1
        if self.phone_extractor.extract(node):
            signals += 1
        if self.address_extractor.extract(node):
            signals += 1
        if self._extract_website(node, ""):
            signals += 1
        return signals

    def _dedupe_nested_blocks(self, blocks: list[Tag]) -> list[Tag]:
        output: list[Tag] = []
        for block in blocks:
            if any(existing in block.parents for existing in output):
                continue
            output = [existing for existing in output if block not in existing.parents]
            output.append(block)
        return output[:80]

    def _extract_from_block(self, block: BeautifulSoup | Tag, source_url: str, fallback_page: bool = False) -> dict:
        emails = self.email_extractor.extract(block)
        phones = self.phone_extractor.extract(block)
        addresses = self.address_extractor.extract(block)
        website = self._extract_website(block, source_url)
        socials = self._extract_socials(block, source_url)
        name = self._extract_name(block) or self._name_from_url(website or source_url)

        entity = {
            "company_name": clean_company_name(name),
            "email": emails[0] if emails else None,
            "emails": emails,
            "phone": phones[0] if phones else None,
            "phone_numbers": phones,
            "address": addresses[0] if addresses else None,
            "addresses": addresses,
            "website": website or None,
            "socials": socials,
            "source_url": source_url,
        }
        entity["confidence"] = entity_confidence(
            entity,
            {
                "same_dom_block": not fallback_page,
                "fallback_page": fallback_page,
            },
        )
        return entity

    def _extract_name(self, node: BeautifulSoup | Tag) -> str:
        selectors = [
            '[itemprop="name"]',
            ".company-name",
            ".business-name",
            ".profile-name",
            ".title",
            "h1",
            "h2",
            "h3",
            "h4",
            'meta[property="og:site_name"]',
            "title",
        ]
        for selector in selectors:
            item = node.select_one(selector)
            if not item:
                continue
            value = item.get("content") if item.name == "meta" else item.get_text(" ")
            cleaned = clean_company_name(value)
            if has_real_entity_name(cleaned):
                return cleaned
        return ""

    def _extract_website(self, node: BeautifulSoup | Tag, source_url: str) -> str:
        source_domain = domain_from_url(source_url)
        for link in node.select("a[href]"):
            href = link.get("href", "")
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            url = normalize_url(href, source_url)
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            if not domain or any(social in domain for social in SOCIAL_DOMAINS):
                continue
            text = clean_text(link.get_text(" ")).lower()
            if source_domain and domain == source_domain and text not in {"website", "visit website", "site"}:
                continue
            return url
        return ""

    def _extract_socials(self, node: BeautifulSoup | Tag, source_url: str) -> list[str]:
        socials: list[str] = []
        for link in node.select("a[href]"):
            url = normalize_url(link.get("href", ""), source_url)
            domain = urlparse(url).netloc.lower()
            if any(social in domain for social in SOCIAL_DOMAINS):
                socials.append(url)
        return unique_keep_order(socials)[:8]

    def _extract_structured_data(self, soup: BeautifulSoup, source_url: str) -> list[dict]:
        entities: list[dict] = []
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or "{}")
            except Exception:
                continue
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict):
                    continue
                graph = item.get("@graph") if isinstance(item.get("@graph"), list) else [item]
                for node in graph:
                    if not isinstance(node, dict):
                        continue
                    node_type = " ".join(node.get("@type", []) if isinstance(node.get("@type"), list) else [str(node.get("@type", ""))])
                    if not any(kind in node_type.lower() for kind in ("organization", "localbusiness", "corporation")):
                        continue
                    address = node.get("address")
                    if isinstance(address, dict):
                        address = ", ".join(clean_text(str(address.get(key, ""))) for key in ("streetAddress", "addressLocality", "addressRegion", "addressCountry") if address.get(key))
                    entity = {
                        "company_name": clean_company_name(node.get("name")),
                        "email": clean_text(node.get("email")).lower() or None,
                        "emails": [clean_text(node.get("email")).lower()] if node.get("email") else [],
                        "phone": self.phone_extractor.normalize(str(node.get("telephone", ""))) or None,
                        "phone_numbers": [self.phone_extractor.normalize(str(node.get("telephone", "")))] if node.get("telephone") else [],
                        "address": clean_text(str(address), 240) or None,
                        "addresses": [clean_text(str(address), 240)] if address else [],
                        "website": normalize_url(str(node.get("url", "")), source_url) or None,
                        "socials": [],
                        "source_url": source_url,
                    }
                    entity["confidence"] = entity_confidence(entity, {"structured_data": True})
                    if self._is_useful_entity(entity):
                        entities.append(entity)
        return entities

    def _name_from_url(self, url: str) -> str:
        domain = domain_from_url(url)
        if not domain:
            return ""
        return clean_company_name(domain.split(".", 1)[0].replace("-", " ").title())

    def _is_useful_entity(self, entity: dict) -> bool:
        if not has_real_entity_name(entity.get("company_name")):
            return False
        return bool(entity.get("email") or entity.get("phone") or entity.get("address") or entity.get("website") or entity.get("socials"))

