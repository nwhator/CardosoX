"""Address extraction scoped to a DOM entity block."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from utils.cleaners import clean_text, unique_keep_order


ADDRESS_HINT_RE = re.compile(
    r"\b(street|st\.?|road|rd\.?|avenue|ave\.?|close|crescent|drive|dr\.?|suite|floor|plot|block|estate|plaza|complex|junction|lagos|abuja|kano|ibadan|port harcourt|nigeria|address|office|location|venue)\b",
    re.I,
)
ADDRESS_LABEL_RE = re.compile(r"\b(address|office|location|venue|branch)\b\s*:?", re.I)
STATE_RE = re.compile(
    r"\b(lagos|abuja|fct|kano|kaduna|rivers|oyo|ogun|enugu|edo|delta|akwa ibom|cross river|kwara|osun|ondo|anambra|imo|abia|plateau|nigeria)\b",
    re.I,
)


class AddressExtractor:
    selectors = [
        "address",
        ".address",
        ".contact-address",
        ".business-address",
        ".location",
        ".venue",
        ".office",
        "[data-address]",
        "[data-location]",
        "[data-venue]",
        "[data-testid*='address']",
        "[data-testid*='location']",
        "[class*='address']",
        "[class*='location']",
        "[class*='venue']",
        "[class*='office']",
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

        for label in node.find_all(string=ADDRESS_LABEL_RE):
            parent = label.parent
            if not parent:
                continue
            labeled_text = clean_text(parent.get_text(" "), 240)
            if labeled_text:
                candidates.append(ADDRESS_LABEL_RE.sub("", labeled_text).strip(" :-"))
            sibling = parent.find_next_sibling()
            if sibling:
                sibling_text = clean_text(sibling.get_text(" "), 240)
                if sibling_text:
                    candidates.append(sibling_text)

        text = node.get_text("\n") if isinstance(node, Tag) else node.get_text("\n")
        for line in [clean_text(line, 240) for line in text.split("\n")]:
            if self._looks_like_address(line):
                candidates.append(line)

        return [address for address in unique_keep_order(candidates) if len(address) >= 10][:5]

    def _looks_like_address(self, line: str) -> bool:
        if not 12 <= len(line) <= 240:
            return False
        if "@" in line:
            return False
        if ADDRESS_HINT_RE.search(line):
            return True
        return "," in line and bool(STATE_RE.search(line))
