"""Entity-aware extraction from company cards, blocks, and rendered pages."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

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
    "[data-company]",
    "[data-business]",
    "[data-listing]",
    "[data-testid*='company']",
    "[data-testid*='business']",
    "[data-testid*='listing']",
    ".company-card",
    ".company",
    ".profile-card",
    ".business-card",
    ".vendor-card",
    ".listing",
    ".directory-item",
    "[class*='company-card']",
    "[class*='business-card']",
    "[class*='vendor-card']",
    "[class*='profile-card']",
    "[class*='listing-card']",
    "[class*='directory-item']",
    "[class*='search-result']",
    "[class*='result-card']",
    "article",
    "li",
    "section",
]
GENERIC_LISTING_CHILD_SELECTORS = ":scope > div, :scope > li, :scope > article, :scope > section, :scope > tr"
CONTAINER_SELECTORS = "main, body, section, article, ul, ol, table, [class*='list'], [class*='grid'], [class*='results'], [class*='directory']"


class EntityExtractor:
    def __init__(self, default_region: str = "NG", ai_client: Any | None = None):
        self.email_extractor = EmailExtractor()
        self.phone_extractor = PhoneExtractor(default_region=default_region)
        self.address_extractor = AddressExtractor()
        self.matcher = EntityMatcher()
        self.ai_client = ai_client
        self.last_ai_quotes: list[dict] = []
        self.last_blocks: list[Tag] = []

    def extract(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        self.last_ai_quotes = []
        blocks = self.detect_company_blocks(soup)
        if not blocks:
            blocks = self._detect_semantic_sections(soup)
        self.last_blocks = blocks

        entities: list[dict] = []
        for block in blocks:
            entity = self._extract_from_block(block, source_url, fallback_page=False)
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
        candidates.extend(self._detect_repeated_listing_blocks(soup))
        return self._dedupe_nested_blocks(candidates)

    def _detect_repeated_listing_blocks(self, soup: BeautifulSoup) -> list[Tag]:
        """Find repeated sibling cards that do not expose useful class names.

        Directory pages often render listings as plain sibling divs. This pass
        prefers those sibling cards over their shared parent so each company
        keeps only its own phone, address, email, website, and socials.
        """
        repeated_blocks: list[Tag] = []
        for container in soup.select(CONTAINER_SELECTORS):
            children = [child for child in container.select(GENERIC_LISTING_CHILD_SELECTORS) if isinstance(child, Tag)]
            viable_children = [child for child in children if self._looks_like_listing_child(child)]
            if len(viable_children) >= 2:
                repeated_blocks.extend(viable_children)
        return repeated_blocks

    def _detect_semantic_sections(self, soup: BeautifulSoup) -> list[Tag]:
        """Use page sections as bounded fallback containers, never the full body."""
        candidates: list[Tag] = []
        selectors = [
            "[class*='contact']",
            "[class*='about']",
            "[class*='profile']",
            "[class*='company']",
            "[class*='business']",
            "[class*='pricing']",
            "[class*='package']",
            "[id*='contact']",
            "[id*='about']",
            "[id*='profile']",
            "[id*='pricing']",
            "address",
            "article",
            "section",
            "main > div",
        ]
        page_text_len = len(clean_text(soup.get_text(" ")))
        for selector in selectors:
            for node in soup.select(selector):
                if not isinstance(node, Tag):
                    continue
                text = clean_text(node.get_text(" "))
                if len(text) < 20:
                    continue
                if page_text_len and len(text) / page_text_len > 0.65:
                    continue
                if self._block_signal_count(node) >= 1:
                    candidates.append(node)
        return self._dedupe_nested_blocks(candidates)[:40]

    def _looks_like_listing_child(self, node: Tag) -> bool:
        text = clean_text(node.get_text(" "))
        if len(text) < 20:
            return False
        if len(text) > 1200:
            return False
        name = self._extract_name(node)
        signals = self._block_signal_count(node)
        contact_count = len(self.email_extractor.extract(node)) + len(self.phone_extractor.extract(node)) + len(self.address_extractor.extract(node))
        return bool(name and (signals >= 2 or contact_count >= 1))

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
        sorted_blocks = sorted(blocks, key=lambda node: len(clean_text(node.get_text(" "))))
        for block in sorted_blocks:
            if any(existing in block.parents for existing in output):
                continue
            if any(existing in block.descendants for existing in output):
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
            "business_name": clean_company_name(name),
            "listing_name": clean_company_name(name),
            "container_path": self._container_path(block),
            "email": emails[0] if emails else None,
            "emails": emails,
            "phone": phones[0] if phones else None,
            "phones": phones,
            "phone_numbers": phones,
            "address": addresses[0] if addresses else None,
            "addresses": addresses,
            "website": website or None,
            "socials": socials,
            "social_links": socials,
            "source_url": source_url,
            "extraction_scope": "page_fallback" if fallback_page else "dom_block",
        }
        entity["confidence"] = entity_confidence(
            entity,
            {
                "same_dom_block": not fallback_page,
                "fallback_page": fallback_page,
            },
        )
        self._apply_ai_resolution(entity, block, source_url)
        return entity

    def _apply_ai_resolution(self, entity: dict, block: BeautifulSoup | Tag, source_url: str) -> None:
        if not self.ai_client:
            return
        try:
            payload = self._build_ai_payload(block, source_url, entity)
            resolved = self.ai_client.resolve_container(payload)
        except Exception as exc:
            logger.debug("AI resolution failed, falling back to local extraction: %s", exc)
            return
        if not resolved:
            return
        for quote in resolved.get("quotes", []):
            quote["company"] = resolved.get("company_name") or entity.get("company_name") or quote.get("company", "")
            quote["source_url"] = source_url
            self.last_ai_quotes.append(quote)

        ai_confidence = float(resolved.get("confidence", 0) or 0)
        if resolved.get("company_name") and (ai_confidence >= 0.35 or not entity.get("company_name")):
            entity["company_name"] = resolved["company_name"]
            entity["business_name"] = resolved["company_name"]
            entity["listing_name"] = resolved["company_name"]
        emails = unique_keep_order([*entity.get("emails", []), *resolved.get("emails", [])])
        phones = unique_keep_order([*entity.get("phone_numbers", []), *(self.phone_extractor.normalize(phone) for phone in resolved.get("phones", []))])
        addresses = unique_keep_order([*entity.get("addresses", []), resolved.get("address", "")])
        socials = unique_keep_order([*entity.get("socials", []), *resolved.get("social_links", [])])

        entity["emails"] = emails
        entity["email"] = emails[0] if emails else entity.get("email")
        entity["phone_numbers"] = [phone for phone in phones if phone]
        entity["phones"] = entity["phone_numbers"]
        entity["phone"] = entity["phone_numbers"][0] if entity["phone_numbers"] else entity.get("phone")
        entity["addresses"] = [address for address in addresses if address]
        entity["address"] = entity["addresses"][0] if entity["addresses"] else entity.get("address")
        if resolved.get("website"):
            entity["website"] = resolved["website"]
        entity["socials"] = socials
        entity["social_links"] = socials
        entity["ai_confidence"] = ai_confidence
        entity["page_type"] = resolved.get("page_type")
        entity["confidence"] = entity_confidence(
            entity,
            {
                "same_dom_block": True,
                "ai_confidence": ai_confidence,
                "semantic_similarity": ai_confidence >= 0.6,
                "header_proximity": bool(payload.get("heading")),
            },
        )
        entity["confidence"] = max(entity["confidence"], round((entity["confidence"] * 0.65) + (ai_confidence * 0.35), 3))

    def _build_ai_payload(self, block: BeautifulSoup | Tag, source_url: str, entity: dict) -> dict:
        heading = ""
        for selector in ("h1", "h2", "h3", "h4", ".title", "[class*='heading']"):
            item = block.select_one(selector) if isinstance(block, Tag) else None
            if item:
                heading = clean_text(item.get_text(" "), 120)
                break
        links = []
        for link in block.select("a[href]") if isinstance(block, Tag) else []:
            links.append({"text": clean_text(link.get_text(" "), 80), "href": normalize_url(link.get("href", ""), source_url)})
        return {
            "source_url": source_url,
            "container_path": self._container_path(block),
            "heading": heading,
            "text": clean_text(block.get_text(" ") if isinstance(block, Tag) else block.get_text(" "), 2200),
            "links": links,
            "traditional": {
                "company_name": entity.get("company_name"),
                "emails": entity.get("emails", []),
                "phones": entity.get("phone_numbers", []),
                "addresses": entity.get("addresses", []),
                "website": entity.get("website"),
                "social_links": entity.get("socials", []),
                "confidence": entity.get("confidence"),
            },
            "dom_signals": {
                "signal_count": self._block_signal_count(block) if isinstance(block, Tag) else 0,
                "same_dom_block": True,
                "header_proximity": bool(heading),
            },
        }

    def _container_path(self, block: BeautifulSoup | Tag) -> str:
        if not isinstance(block, Tag):
            return ""
        parts = []
        node: Tag | None = block
        while isinstance(node, Tag) and node.name not in {"[document]", "html"} and len(parts) < 6:
            label = node.name
            node_id = node.get("id")
            classes = node.get("class") or []
            if node_id:
                label += f"#{node_id}"
            elif classes:
                label += "." + ".".join(str(item) for item in classes[:2])
            parts.append(label)
            node = node.parent if isinstance(node.parent, Tag) else None
        return " > ".join(reversed(parts))

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
            'a[href*="company"]',
            'a[href*="profile"]',
            'a[href*="business"]',
            'a[href*="listing"]',
            '[class*="company"][class*="name"]',
            '[class*="business"][class*="name"]',
            '[class*="listing"][class*="name"]',
            '[class*="vendor"][class*="name"]',
            '[class*="profile"][class*="name"]',
            '[class*="title"]',
            '[class*="heading"]',
            '[class*="card-title"]',
            '[class*="result-title"]',
            "strong",
            "b",
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
        aria = clean_company_name(node.get("aria-label") if isinstance(node, Tag) else "")
        if has_real_entity_name(aria):
            return aria
        img = node.select_one("img[alt]")
        if img:
            cleaned = clean_company_name(img.get("alt"))
            if has_real_entity_name(cleaned):
                return cleaned
        text = clean_text(node.get_text("\n") if isinstance(node, Tag) else node.get_text("\n"))
        for line in text.split("\n"):
            candidate = clean_company_name(line)
            if has_real_entity_name(candidate) and self._looks_like_name_line(candidate):
                return candidate
        return ""

    def _looks_like_name_line(self, value: str) -> bool:
        if not 2 <= len(value) <= 90:
            return False
        if "@" in value or re.search(r"\d{5,}", value):
            return False
        if re.search(r"\b(street|road|avenue|lagos|abuja|nigeria|phone|email|address|price|from)\b", value, re.I):
            return False
        return True

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
                        "business_name": clean_company_name(node.get("name")),
                        "listing_name": clean_company_name(node.get("name")),
                        "email": clean_text(node.get("email")).lower() or None,
                        "emails": [clean_text(node.get("email")).lower()] if node.get("email") else [],
                        "phone": self.phone_extractor.normalize(str(node.get("telephone", ""))) or None,
                        "phones": [self.phone_extractor.normalize(str(node.get("telephone", "")))] if node.get("telephone") else [],
                        "phone_numbers": [self.phone_extractor.normalize(str(node.get("telephone", "")))] if node.get("telephone") else [],
                        "address": clean_text(str(address), 240) or None,
                        "addresses": [clean_text(str(address), 240)] if address else [],
                        "website": normalize_url(str(node.get("url", "")), source_url) or None,
                        "socials": [],
                        "social_links": [],
                        "source_url": source_url,
                        "extraction_scope": "structured_data",
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
