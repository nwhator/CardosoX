"""Normalization utilities for extracted data."""

from __future__ import annotations

import base64
import re
from typing import Optional
from urllib.parse import urlparse


EMAIL_OBFUSCATIONS = [
    (r"\s*\[at\]\s*", "@"),
    (r"\s*\(at\)\s*", "@"),
    (r"\s+at\s+", "@"),
    (r"\s*\[dot\]\s*", "."),
    (r"\s*\(dot\)\s*", "."),
    (r"\s+dot\s+", "."),
]


def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def normalize_email(value: str) -> Optional[str]:
    if not value:
        return None
    email = value.strip().lower()
    email = re.sub(r"^mailto:", "", email)
    for pattern, replacement in EMAIL_OBFUSCATIONS:
        email = re.sub(pattern, replacement, email, flags=re.IGNORECASE)
    email = email.replace(" ", "")
    return email or None


def normalize_phone(value: str) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    raw = raw.replace("whatsapp", "")
    raw = re.sub(r"ext\.?\s*\d+", "", raw, flags=re.IGNORECASE)
    raw = raw.strip()
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if raw.startswith("+"):
        return "+" + digits
    if len(digits) >= 10 and len(digits) <= 15:
        return digits
    if len(digits) >= 7:
        return digits
    return None


def normalize_address(value: str) -> Optional[str]:
    if not value:
        return None
    normalized = clean_text(value)
    if len(normalized) < 5:
        return None
    return normalized


def normalize_url(value: str) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("//"):
        value = "https:" + value
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    try:
        parsed = urlparse(value)
    except Exception:
        return None
    if not parsed.netloc:
        return None
    return value


def normalize_social_url(value: str) -> Optional[str]:
    url = normalize_url(value)
    if not url:
        return None
    return url


def decode_base64_string(value: str) -> Optional[str]:
    if not value:
        return None
    try:
        decoded = base64.b64decode(value).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return None
