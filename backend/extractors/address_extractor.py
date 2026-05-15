"""Address extraction utilities."""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup

from extractors.base import ExtractedValue
from extractors.jsonld_extractor import extract_organizations
from utils.cleaners import normalize_address
from utils.scoring import score_confidence


POSTAL_REGEX = re.compile(r"\b\d{4,6}(?:-\d{4})?\b")


def extract_addresses(html: str, soup: BeautifulSoup) -> List[ExtractedValue]:
    extracted: List[ExtractedValue] = []

    for org in extract_organizations(soup):
        address = org.get("address")
        if isinstance(address, dict):
            parts = [
                address.get("streetAddress"),
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("postalCode"),
                address.get("addressCountry"),
            ]
            text = ", ".join([p for p in parts if p])
            normalized = normalize_address(text)
            if normalized:
                extracted.append(ExtractedValue(normalized, score_confidence("jsonld"), "jsonld"))

    for element in soup.select("address, .address, .contact-address, .location, [data-address]"):
        text = normalize_address(element.get_text(" ", strip=True))
        if text:
            extracted.append(ExtractedValue(text, score_confidence("dom"), "dom", element))

    for line in html.split("\n"):
        if POSTAL_REGEX.search(line) and len(line.strip()) > 15:
            normalized = normalize_address(line)
            if normalized:
                extracted.append(ExtractedValue(normalized, score_confidence("regex"), "regex"))

    return _dedupe(extracted)


def _dedupe(values: List[ExtractedValue]) -> List[ExtractedValue]:
    seen = set()
    unique: List[ExtractedValue] = []
    for item in values:
        if item.value in seen:
            continue
        seen.add(item.value)
        unique.append(item)
    return unique
