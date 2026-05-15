"""Email extraction utilities."""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup

from extractors.base import ExtractedValue
from utils.cleaners import normalize_email, decode_base64_string
from utils.scoring import score_confidence
from utils.validators import is_valid_email


EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
BASE64_REGEX = re.compile(r"(?:[A-Za-z0-9+/]{16,}={0,2})")


def _decode_cloudflare_email(encoded: str) -> str:
    try:
        key = int(encoded[:2], 16)
    except Exception:
        return ""
    decoded_chars = []
    for i in range(2, len(encoded), 2):
        try:
            decoded_chars.append(chr(int(encoded[i:i + 2], 16) ^ key))
        except Exception:
            return ""
    return "".join(decoded_chars)


def extract_emails(html: str, soup: BeautifulSoup) -> List[ExtractedValue]:
    extracted: List[ExtractedValue] = []

    # mailto links
    for link in soup.select('a[href^="mailto:"]'):
        href = link.get("href", "")
        email = normalize_email(href)
        if email and is_valid_email(email):
            extracted.append(ExtractedValue(email, score_confidence("mailto"), "mailto", link))

    # Cloudflare protected emails
    for span in soup.select("[data-cfemail]"):
        encoded = span.get("data-cfemail")
        decoded = _decode_cloudflare_email(encoded or "")
        email = normalize_email(decoded)
        if email and is_valid_email(email):
            extracted.append(ExtractedValue(email, score_confidence("cloudflare"), "cloudflare", span))

    # regex fallback
    for match in EMAIL_REGEX.findall(html):
        email = normalize_email(match)
        if email and is_valid_email(email):
            extracted.append(ExtractedValue(email, score_confidence("regex"), "regex"))

    # base64 encoded emails
    for match in BASE64_REGEX.findall(html):
        decoded = decode_base64_string(match)
        if not decoded or "@" not in decoded:
            continue
        email = normalize_email(decoded)
        if email and is_valid_email(email):
            extracted.append(ExtractedValue(email, score_confidence("base64"), "base64"))

    # de-obfuscate script strings like name [at] domain [dot] com
    for text in soup.stripped_strings:
        if "@" in text:
            continue
        if "at" in text.lower() and "dot" in text.lower():
            candidate = normalize_email(text)
            if candidate and is_valid_email(candidate):
                extracted.append(ExtractedValue(candidate, score_confidence("script"), "script"))

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
