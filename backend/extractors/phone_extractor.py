"""Phone extraction and best-effort E.164 normalization."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

from utils.cleaners import clean_text, unique_keep_order

try:
    import phonenumbers
except Exception:  # pragma: no cover - optional dependency fallback
    phonenumbers = None


PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s().-]?)?(?:\(?\d{2,5}\)?[\s().-]?){2,5}\d{2,5}")


class PhoneExtractor:
    def __init__(self, default_region: str = "NG"):
        self.default_region = default_region

    def normalize(self, phone: str) -> str:
        value = clean_text(phone)
        if not value:
            return ""
        value = re.sub(r"(?i)\b(ext|extension|x)\.?\s*\d+$", "", value).strip()
        if phonenumbers:
            try:
                parsed = phonenumbers.parse(value, self.default_region)
                if phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed):
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            except Exception:
                pass

        digits = re.sub(r"\D", "", value)
        if len(digits) < 7 or len(digits) > 15:
            return ""
        if value.startswith("+"):
            return "+" + digits
        if self.default_region == "NG" and digits.startswith("0") and len(digits) == 11:
            return "+234" + digits[1:]
        return "+" + digits if len(digits) > 10 else digits

    def extract(self, node: BeautifulSoup | Tag) -> list[str]:
        candidates: list[str] = []

        for link in node.select('a[href^="tel:"]'):
            candidates.append(link.get("href", "").split(":", 1)[-1])

        for link in node.select('a[href*="wa.me/"], a[href*="whatsapp.com/send"]'):
            href = link.get("href", "")
            parsed = urlparse(href)
            if "wa.me" in parsed.netloc:
                candidates.append(parsed.path.strip("/"))
            qs_phone = parse_qs(parsed.query).get("phone", [])
            candidates.extend(qs_phone)

        text = clean_text(node.get_text(" ") if isinstance(node, Tag) else node.get_text(" "))
        candidates.extend(PHONE_RE.findall(text))
        normalized = [self.normalize(candidate) for candidate in candidates]
        return [phone for phone in unique_keep_order(normalized) if phone]

