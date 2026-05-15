"""Cleaning helpers shared by crawlers and extractors."""

from __future__ import annotations

import html
import re
from typing import Iterable, TypeVar
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

T = TypeVar("T")


WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str | None, max_length: int | None = None) -> str:
    if not value:
        return ""
    cleaned = html.unescape(value)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip(" \t\r\n:|-")
    if max_length and len(cleaned) > max_length:
        return cleaned[:max_length].rstrip()
    return cleaned


def clean_company_name(value: str | None) -> str:
    name = clean_text(value, 120)
    if not name:
        return ""
    name = re.sub(r"\b(home|about us|contact us|pricing|services)\b$", "", name, flags=re.I)
    name = name.strip(" \t\r\n-|:")
    if len(name) < 2:
        return ""
    return name


def unique_keep_order(values: Iterable[T]) -> list[T]:
    seen: set[str] = set()
    output: list[T] = []
    for value in values:
        key = str(value).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def normalize_url(url: str, base_url: str | None = None) -> str:
    if not url:
        return ""
    url = html.unescape(url.strip())
    if base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    if not parsed.scheme and parsed.netloc:
        parsed = parsed._replace(scheme="https")
    if not parsed.scheme and parsed.path:
        parsed = urlparse("https://" + url)
    clean, _fragment = urldefrag(urlunparse(parsed))
    return clean.rstrip("/")


def domain_from_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return parsed.netloc.lower().removeprefix("www.")


def looks_like_asset(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".pdf",
            ".zip",
            ".css",
            ".js",
            ".ico",
            ".woff",
            ".woff2",
            ".ttf",
        )
    )

