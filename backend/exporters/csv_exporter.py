"""CSV export helpers for entity-aware crawl results."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path


class CsvExporter:
    fieldnames = [
        "source_url",
        "company_name",
        "business_name",
        "listing_name",
        "email",
        "phone",
        "address",
        "website",
        "socials",
        "confidence",
        "quote_title",
        "quote_price",
        "quote_currency",
        "quote_confidence",
    ]

    def dumps(self, results: list[dict]) -> str:
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.fieldnames)
        writer.writeheader()
        for result in results:
            for company in result.get("companies", []):
                writer.writerow(
                    {
                        "source_url": company.get("source_url") or result.get("source_url"),
                        "company_name": company.get("company_name"),
                        "business_name": company.get("business_name"),
                        "listing_name": company.get("listing_name"),
                        "email": company.get("email"),
                        "phone": company.get("phone"),
                        "address": company.get("address"),
                        "website": company.get("website"),
                        "socials": "; ".join(company.get("socials", [])),
                        "confidence": company.get("confidence"),
                    }
                )
            for quote in result.get("quotes", []):
                writer.writerow(
                    {
                        "source_url": quote.get("source_url") or result.get("source_url"),
                        "company_name": quote.get("company"),
                        "quote_title": quote.get("title"),
                        "quote_price": quote.get("price"),
                        "quote_currency": quote.get("currency"),
                        "quote_confidence": quote.get("confidence"),
                    }
                )
        return buffer.getvalue()

    def save(self, results: list[dict], path: str | Path) -> None:
        Path(path).write_text(self.dumps(results), encoding="utf-8", newline="")
