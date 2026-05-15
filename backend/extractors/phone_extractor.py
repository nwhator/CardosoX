"""Phone extraction utilities."""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup

from extractors.base import ExtractedValue
from utils.cleaners import normalize_phone
from utils.scoring import score_confidence
from utils.validators import is_valid_phone


PHONE_REGEX = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
WHATSAPP_REGEX = re.compile(r"wa\.me/(\d+)")


def extract_phones(html: str, soup: BeautifulSoup) -> List[ExtractedValue]:
    extracted: List[ExtractedValue] = []

    for link in soup.select('a[href^="tel:"]'):
        href = link.get("href", "")
        number = normalize_phone(href.replace("tel:", ""))
        if number and is_valid_phone(number):
            extracted.append(ExtractedValue(number, score_confidence("tel"), "tel", link))

    for link in soup.select('a[href*="wa.me/"]'):
        href = link.get("href", "")
        match = WHATSAPP_REGEX.search(href)
        if match:
            number = normalize_phone(match.group(1))
            if number and is_valid_phone(number):
                extracted.append(ExtractedValue(number, score_confidence("whatsapp"), "whatsapp", link))

    for match in PHONE_REGEX.findall(html):
        number = normalize_phone(match)
        if number and is_valid_phone(number):
            extracted.append(ExtractedValue(number, score_confidence("regex"), "regex"))

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
