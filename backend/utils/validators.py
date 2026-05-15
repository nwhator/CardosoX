"""Validation helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    url = url.strip()
    url_pattern = r"^(https?://)?([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}.*$"
    if not re.match(url_pattern, url, re.IGNORECASE):
        return False
    try:
        parsed = urlparse(url if url.startswith(("http://", "https://")) else "https://" + url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def validate_urls(urls: List[str]) -> Dict[str, Any]:
    if not urls:
        return {"valid": False, "message": "No URLs provided"}
    if not isinstance(urls, list):
        return {"valid": False, "message": "URLs must be a list"}
    if len(urls) > 10:
        return {"valid": False, "message": "Maximum 10 URLs allowed per request"}

    valid_urls: List[str] = []
    invalid_urls: List[str] = []

    for url in urls:
        url = url.strip() if isinstance(url, str) else url
        if not url:
            continue
        if is_valid_url(url):
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            valid_urls.append(url)
        else:
            invalid_urls.append(url)

    if not valid_urls:
        return {"valid": False, "message": "No valid URLs found"}

    result: Dict[str, Any] = {
        "valid": True,
        "message": "All URLs are valid",
        "valid_urls": valid_urls,
        "count": len(valid_urls),
    }
    if invalid_urls:
        result["message"] = f"Validated {len(valid_urls)} URLs. {len(invalid_urls)} invalid."
        result["invalid_urls"] = invalid_urls
    return result


def is_valid_email(value: str) -> bool:
    if not value:
        return False
    return bool(EMAIL_PATTERN.match(value))


def is_valid_phone(value: str) -> bool:
    if not value:
        return False
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 7


def is_probable_company_link(url: str, base_domain: Optional[str], patterns: List[str]) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if base_domain and parsed.netloc and base_domain not in parsed.netloc:
        return False
    path = parsed.path.lower()
    if any(pattern in path for pattern in patterns):
        return True
    return False


def is_social_link(url: str) -> bool:
    if not url:
        return False
    social_domains = (
        "facebook.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "youtube.com",
        "tiktok.com",
    )
    return any(domain in url for domain in social_domains)
