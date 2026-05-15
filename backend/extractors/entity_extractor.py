"""Entity extraction using DOM-based grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from extractors.address_extractor import extract_addresses
from extractors.base import ExtractedValue
from extractors.email_extractor import extract_emails
from extractors.jsonld_extractor import extract_organizations
from extractors.phone_extractor import extract_phones
from matchers.entity_matcher import EntityMatcher
from utils.cleaners import normalize_address, normalize_social_url, normalize_url
from utils.scoring import score_confidence
from utils.validators import is_social_link


@dataclass
class FieldValue:
    value: str
    confidence: float


@dataclass
class CompanyEntity:
    name: Optional[FieldValue]
    emails: List[FieldValue]
    phones: List[FieldValue]
    address: Optional[FieldValue]
    website: Optional[FieldValue]
    social_links: List[FieldValue]
    source_url: str
    confidence: float
    block: Optional[Tag] = field(repr=False, default=None)

    def to_dict(self) -> dict:
        return {
            "name": _field_to_dict(self.name),
            "emails": [_field_to_dict(item) for item in self.emails],
            "phones": [_field_to_dict(item) for item in self.phones],
            "address": _field_to_dict(self.address),
            "website": _field_to_dict(self.website),
            "social_links": [_field_to_dict(item) for item in self.social_links],
            "source_url": self.source_url,
            "confidence": self.confidence,
        }


def _field_to_dict(field_value: Optional[FieldValue]) -> Optional[dict]:
    if not field_value:
        return None
    return {"value": field_value.value, "confidence": field_value.confidence}


class EntityExtractor:
    def __init__(self) -> None:
        self.matcher = EntityMatcher()

    def extract(self, html: str, source_url: str) -> List[CompanyEntity]:
        soup = BeautifulSoup(html, "lxml")
        blocks = self._identify_company_blocks(soup)
        org_data = extract_organizations(soup)
        fallback_name = self._organization_name(org_data)
        base_domain = urlparse(source_url).netloc

        entities: List[CompanyEntity] = []
        for block in blocks:
            block_html = str(block)
            block_soup = BeautifulSoup(block_html, "lxml")
            name_value, name_element = self._extract_name(block_soup, fallback_name)
            emails = extract_emails(block_html, block_soup)
            phones = extract_phones(block_html, block_soup)
            addresses = extract_addresses(block_html, block_soup)
            website = self._extract_website(block_soup, source_url, base_domain)
            social_links = self._extract_social_links(block_soup)

            emails = self.matcher.adjust_values(emails, name_element)
            phones = self.matcher.adjust_values(phones, name_element)
            addresses = self.matcher.adjust_values(addresses, name_element)

            entity = CompanyEntity(
                name=self._wrap_field(name_value),
                emails=[self._wrap_field(item) for item in emails],
                phones=[self._wrap_field(item) for item in phones],
                address=self._wrap_field(addresses[0]) if addresses else None,
                website=self._wrap_field(website) if website else None,
                social_links=[self._wrap_field(item) for item in social_links],
                source_url=source_url,
                confidence=0.0,
                block=block,
            )
            entity = self.matcher.finalize_entity(entity)
            entities.append(entity)

        return entities

    def _identify_company_blocks(self, soup: BeautifulSoup) -> List[Tag]:
        candidates = soup.find_all(["article", "section", "div", "li"], limit=2000)
        grouped: dict[Tuple[str, str], List[Tag]] = {}
        for tag in candidates:
            classes = " ".join(sorted(tag.get("class", [])))
            signature = (tag.name, classes)
            if not classes:
                continue
            grouped.setdefault(signature, []).append(tag)

        grouped = {key: value for key, value in grouped.items() if len(value) >= 2}
        if grouped:
            signature = max(grouped.items(), key=lambda item: len(item[1]))[0]
            return grouped[signature]

        org_blocks = soup.select('[itemtype*="Organization"], [itemtype*="LocalBusiness"]')
        if org_blocks:
            return list(org_blocks)

        body = soup.body
        return [body] if body else [soup]

    def _extract_name(self, soup: BeautifulSoup, fallback_name: Optional[str]) -> Tuple[Optional[ExtractedValue], Optional[Tag]]:
        for selector in ["h1", "h2", "h3", "h4", ".company-name", ".business-name", "[data-company]"]:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                name = element.get_text(strip=True)
                return ExtractedValue(name, score_confidence("heading"), "heading", element), element
        if fallback_name:
            return ExtractedValue(fallback_name, score_confidence("fallback"), "fallback"), None
        title_tag = soup.select_one("title")
        if title_tag and title_tag.get_text(strip=True):
            return ExtractedValue(title_tag.get_text(strip=True), score_confidence("fallback"), "fallback"), title_tag
        return None, None

    def _extract_website(self, soup: BeautifulSoup, source_url: str, base_domain: str) -> Optional[ExtractedValue]:
        for link in soup.select('a[href^="http"]'):
            href = normalize_url(link.get("href", ""))
            if not href:
                continue
            if is_social_link(href):
                continue
            if base_domain and base_domain not in href:
                return ExtractedValue(href, score_confidence("dom"), "dom", link)
        return ExtractedValue(source_url, score_confidence("fallback"), "fallback")

    def _extract_social_links(self, soup: BeautifulSoup) -> List[ExtractedValue]:
        socials: List[ExtractedValue] = []
        for link in soup.select('a[href^="http"]'):
            href = normalize_social_url(link.get("href", ""))
            if not href or not is_social_link(href):
                continue
            socials.append(ExtractedValue(href, score_confidence("dom"), "dom", link))
        return socials

    def _organization_name(self, organizations: List[dict]) -> Optional[str]:
        for org in organizations:
            if "name" in org:
                return str(org.get("name"))
        return None

    def _wrap_field(self, item: ExtractedValue | None) -> Optional[FieldValue]:
        if not item:
            return None
        value = item.value
        if not value:
            return None
        if item.source == "dom" and item.value:
            address = normalize_address(item.value)
            value = address or item.value
        return FieldValue(value=value, confidence=item.confidence)
