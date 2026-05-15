"""Email extraction with entity-block scoping and common obfuscation decoders."""

from __future__ import annotations

import base64
import binascii
import re
from html import unescape
from typing import Iterable

from bs4 import BeautifulSoup, Tag

from utils.cleaners import clean_text, unique_keep_order
from utils.validators import is_valid_email


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-']+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
BASE64_RE = re.compile(r"\b(?:[A-Za-z0-9+/]{12,}={0,2})\b")


def decode_cloudflare_email(encoded: str) -> str:
    try:
        key = int(encoded[:2], 16)
        return "".join(chr(int(encoded[i : i + 2], 16) ^ key) for i in range(2, len(encoded), 2))
    except Exception:
        return ""


def deobfuscate_text(text: str) -> str:
    value = unescape(text)
    replacements = [
        (r"\s*\[\s*at\s*\]\s*", "@"),
        (r"\s*\(\s*at\s*\)\s*", "@"),
        (r"\s+\bat\b\s+", "@"),
        (r"\s*\[\s*dot\s*\]\s*", "."),
        (r"\s*\(\s*dot\s*\)\s*", "."),
        (r"\s+\bdot\b\s+", "."),
    ]
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.I)
    return value


def _decode_possible_base64(tokens: Iterable[str]) -> list[str]:
    decoded: list[str] = []
    for token in tokens:
        try:
            raw = base64.b64decode(token, validate=True)
            text = raw.decode("utf-8", errors="ignore")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if "@" in text:
            decoded.append(text)
    return decoded


class EmailExtractor:
    def extract(self, node: BeautifulSoup | Tag) -> list[str]:
        candidates: list[str] = []

        for link in node.select('a[href^="mailto:"]'):
            href = link.get("href", "")
            email = href.split(":", 1)[-1].split("?", 1)[0]
            candidates.append(email)

        for cf_node in node.select("[data-cfemail]"):
            decoded = decode_cloudflare_email(cf_node.get("data-cfemail", ""))
            if decoded:
                candidates.append(decoded)

        for link in node.select('a[href*="/cdn-cgi/l/email-protection#"]'):
            href = link.get("href", "")
            encoded = href.rsplit("#", 1)[-1]
            decoded = decode_cloudflare_email(encoded)
            if decoded:
                candidates.append(decoded)

        html = str(node)
        text = deobfuscate_text(clean_text(node.get_text(" ") if isinstance(node, Tag) else node.get_text(" ")))
        candidates.extend(EMAIL_RE.findall(deobfuscate_text(unescape(html))))
        candidates.extend(EMAIL_RE.findall(text))
        candidates.extend(EMAIL_RE.findall(" ".join(_decode_possible_base64(BASE64_RE.findall(html)))))

        normalized = [clean_text(email).lower() for email in candidates]
        return [email for email in unique_keep_order(normalized) if is_valid_email(email)]

