"""Compatibility exports plus crawler utility package."""

from __future__ import annotations

from .cleaners import clean_company_name, clean_text, domain_from_url, normalize_url, unique_keep_order
from .validators import is_valid_email, is_valid_url, validate_urls


def sanitize_email(email: str) -> str | None:
    value = clean_text(email).lower()
    return value if is_valid_email(value) else None


def sanitize_phone(phone: str) -> str | None:
    value = "".join(c for c in clean_text(phone) if c.isdigit() or c in "+-() ")
    digits = "".join(c for c in value if c.isdigit())
    return value if len(digits) >= 7 else None


def sanitize_address(address: str) -> str | None:
    value = clean_text(address)
    return value if len(value) >= 5 else None


def format_response(status: str, results: list[dict] | None = None, message: str | None = None) -> dict:
    response = {"status": status}
    if results:
        response["results"] = results
        response["count"] = len(results)
    if message:
        response["message"] = message
    return response


def create_csv_header() -> str:
    return "Source URL,Company Name,Business Name,Listing Name,Email,Phone,Address,Website,Socials,Confidence,Status"


def create_csv_row(data: dict) -> str:
    def escape_csv(value):
        if value is None:
            return ""
        text = str(value)
        if "," in text or '"' in text or "\n" in text:
            text = '"' + text.replace('"', '""') + '"'
        return text

    return ",".join(
        [
            escape_csv(data.get("source_url") or data.get("url")),
            escape_csv(data.get("company_name")),
            escape_csv(data.get("business_name")),
            escape_csv(data.get("listing_name")),
            escape_csv(data.get("email")),
            escape_csv(data.get("phone")),
            escape_csv(data.get("address")),
            escape_csv(data.get("website")),
            escape_csv("; ".join(data.get("socials", []))),
            escape_csv(data.get("confidence")),
            escape_csv(data.get("status")),
        ]
    )
