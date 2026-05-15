"""Attach quotes to likely companies using local page context."""

from __future__ import annotations

from difflib import SequenceMatcher


class QuoteMatcher:
    def match(self, quotes: list[dict], companies: list[dict]) -> list[dict]:
        if not quotes or not companies:
            return quotes
        if len(companies) == 1:
            for quote in quotes:
                quote["company"] = companies[0].get("company_name", "")
            return quotes

        for quote in quotes:
            quote_text = " ".join(str(quote.get(key, "")) for key in ("title", "description")).lower()
            best_company = ""
            best_score = 0.0
            for company in companies:
                name = str(company.get("company_name", ""))
                score = SequenceMatcher(None, name.lower(), quote_text).ratio() if name else 0.0
                if name.lower() in quote_text:
                    score += 0.5
                if score > best_score:
                    best_score = score
                    best_company = name
            quote["company"] = best_company if best_score >= 0.35 else ""
        return quotes

