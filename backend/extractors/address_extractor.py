"""Address extraction scoped to a DOM entity block."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from utils.cleaners import clean_text, unique_keep_order


ADDRESS_HINT_RE = re.compile(
    r"\b(street|road|rd\.?|avenue|ave\.?|close|crescent|drive|suite|floor|plot|lagos|abuja|nigeria|address|office)\b",
    re.I,
)


class AddressExtractor:
    selectors = [
        "address",
        ".address",
        ".contact-address",
        ".business-address",
        ".location",
        "[data-address]",
        '[itemprop*="address"]',
    ]

    def extract(self, node: BeautifulSoup | Tag) -> list[str]:
        candidates: list[str] = []

        for selector in self.selectors:
            for item in node.select(selector):
                text = clean_text(item.get_text(" "), 240)
                if text:
                    candidates.append(text)

        for item in node.select('[itemprop="streetAddress"], [itemprop="addressLocality"], [itemprop="addressRegion"]'):
            text = clean_text(item.get_text(" "), 160)
            if text:
                candidates.append(text)

        text = node.get_text("\n") if isinstance(node, Tag) else node.get_text("\n")
        for line in [clean_text(line, 240) for line in text.split("\n")]:
            if 12 <= len(line) <= 240 and ADDRESS_HINT_RE.search(line):
                candidates.append(line)

        return [address for address in unique_keep_order(candidates) if len(address) >= 10][:5]
