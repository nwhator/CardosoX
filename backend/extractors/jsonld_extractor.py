"""Extract JSON-LD structured data."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from bs4 import BeautifulSoup


def extract_jsonld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            content = script.string or script.get_text()
            if not content:
                continue
            loaded = json.loads(content)
            if isinstance(loaded, list):
                data.extend(_flatten(loaded))
            elif isinstance(loaded, dict):
                data.extend(_flatten([loaded]))
        except Exception:
            continue
    return data


def extract_organizations(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    organizations: List[Dict[str, Any]] = []
    for item in extract_jsonld(soup):
        item_type = item.get("@type") or item.get("@type", "")
        if isinstance(item_type, list):
            item_type = " ".join(item_type)
        if "Organization" in str(item_type) or "LocalBusiness" in str(item_type):
            organizations.append(item)
    return organizations


def _flatten(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for item in items:
        if "@graph" in item and isinstance(item["@graph"], list):
            flattened.extend(item["@graph"])
        else:
            flattened.append(item)
    return flattened
