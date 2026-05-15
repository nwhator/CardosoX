"""Validation helpers for URLs, emails, and extracted entities."""

from __future__ import annotations

import re
from urllib.parse import urlparse


EMAIL_RE = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
URL_RE = re.compile(r"^(https?://)?([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}.*$", re.I)

NOISE_EMAIL_PARTS = (
    "example.com",
    "test.com",
    "domain.com",
    "placeholder",
    "email.com",
    "yourname",
    "youremail",
    "name@",
)


def is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    if len(email) > 254 or any(part in email for part in NOISE_EMAIL_PARTS):
        return False
    if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return False
    return bool(EMAIL_RE.match(email))


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    value = url.strip()
    if not URL_RE.match(value):
        return False
    try:
        parsed = urlparse(value if value.startswith(("http://", "https://")) else "https://" + value)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def validate_urls(urls: list[str]) -> dict:
    if not urls:
        return {"valid": False, "message": "No URLs provided"}
    if not isinstance(urls, list):
        return {"valid": False, "message": "URLs must be a list"}
    if len(urls) > 10:
        return {"valid": False, "message": "Maximum 10 URLs allowed per request"}

    valid_urls: list[str] = []
    invalid_urls: list[str] = []
    for url in urls:
        value = url.strip() if isinstance(url, str) else url
        if not value:
            continue
        if is_valid_url(value):
            if not value.startswith(("http://", "https://")):
                value = "https://" + value
            valid_urls.append(value)
        else:
            invalid_urls.append(value)

    if not valid_urls:
        return {"valid": False, "message": "No valid URLs found"}

    result = {
        "valid": True,
        "message": "All URLs are valid",
        "valid_urls": valid_urls,
        "count": len(valid_urls),
    }
    if invalid_urls:
        result["message"] = f"Validated {len(valid_urls)} URLs. {len(invalid_urls)} invalid."
        result["invalid_urls"] = invalid_urls
    return result


def has_real_entity_name(name: str | None) -> bool:
    if not name:
        return False
    normalized = name.strip().lower()
    if len(normalized) < 2:
        return False
    return normalized not in {"home", "about", "contact", "services", "pricing", "login", "sign in"}

