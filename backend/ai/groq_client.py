"""GROQ-backed entity resolution and crawl prioritization.

The client deliberately accepts only compact DOM-container payloads or URL
metadata. It never receives a full page body.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import requests

from utils.cleaners import clean_text, normalize_url, unique_keep_order
from utils.validators import has_real_entity_name, is_valid_email

logger = logging.getLogger(__name__)


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_FALLBACK_MODEL = "llama-3.1-8b-instant"


ENTITY_SYSTEM_PROMPT = """You resolve business entities from one DOM container only.
Return structured JSON only. Do not invent facts. Keep emails, phones, addresses,
websites, social links, and quotes attached only when they belong to the same
business in this container. Reject category names, navigation labels, spam,
placeholders, forms, and generic headings."""

ENTITY_USER_PROMPT = """Resolve the business entity and quotes from this DOM container.

Rules:
- Use only the supplied container text, links, and local extractor candidates.
- If multiple businesses appear, choose the primary business in this container.
- If the container is not a real business, return company_name "" and confidence 0.
- Output JSON with exactly these top-level keys:
  company_name, emails, phones, address, website, social_links, confidence, page_type, quotes.
- quotes is an array of {title, price, currency, description, confidence}.

Container:
{payload}"""


PAGE_SYSTEM_PROMPT = """Classify crawl targets for business intelligence extraction.
Return JSON only. Score URLs likely to contain contacts, pricing, addresses,
team/company details, profile pages, or business data. Do not fetch pages."""


PAGE_USER_PROMPT = """Score these links from 0.0 to 1.0 for crawl priority.
Prioritize /contact, /about, /pricing, /team, /company, /profile, addresses,
business data, services, packages, and quotes.
Return JSON: {"pages":[{"url":"","score":0.0,"reason":""}]}.

Links:
{payload}"""


class GroqClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self.fallback_model = os.getenv("GROQ_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL).strip() or DEFAULT_FALLBACK_MODEL
        self.enabled = os.getenv("ENABLE_AI_MATCHING", "true").lower() == "true" and bool(self.api_key)
        self.quote_enabled = os.getenv("ENABLE_QUOTE_CRAWLER", "true").lower() == "true"
        self.timeout = int(os.getenv("GROQ_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("GROQ_RETRIES", "2"))
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache")) / "groq"
        self.session = requests.Session()

    def resolve_container(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        compact = self._compact_payload(payload)
        if not compact.get("text") and not compact.get("links") and not compact.get("traditional"):
            return None
        cache_key = self._cache_key("entity", compact)
        cached = self._read_cache(cache_key)
        if cached is not None:
            return self._normalize_entity_response(cached, payload.get("source_url", ""))

        response = self._chat_json(
            system_prompt=ENTITY_SYSTEM_PROMPT,
            user_prompt=ENTITY_USER_PROMPT.format(payload=json.dumps(compact, ensure_ascii=False)),
            cache_key=cache_key,
        )
        # Validate the model output is a dict before attempting normalization.
        if response is None:
            return None
        if not isinstance(response, dict):
            logger.warning("GROQ returned non-dict response for %s: %r", cache_key, response)
            return None
        normalized = self._normalize_entity_response(response, payload.get("source_url", ""))
        self._write_cache(cache_key, normalized)
        return normalized

    def score_pages(self, urls: list[str]) -> dict[str, float]:
        if not self.enabled or not urls:
            return {}
        unique_urls = unique_keep_order(urls)[:40]
        payload = [{"url": url, "path": normalize_url(url)} for url in unique_urls]
        cache_key = self._cache_key("pages", payload)
        cached = self._read_cache(cache_key)
        if cached is None:
            cached = self._chat_json(
                system_prompt=PAGE_SYSTEM_PROMPT,
                user_prompt=PAGE_USER_PROMPT.format(payload=json.dumps(payload, ensure_ascii=False)),
                cache_key=cache_key,
                max_tokens=1200,
            )
            if cached is not None:
                self._write_cache(cache_key, cached)
        if not isinstance(cached, dict):
            return {}
        scores: dict[str, float] = {}
        for item in cached.get("pages", []):
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", ""))
            try:
                scores[url] = max(0.0, min(1.0, float(item.get("score", 0))))
            except (TypeError, ValueError):
                continue
        return scores

    def _chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        cache_key: str,
        max_tokens: int = 1800,
    ) -> dict[str, Any] | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        models = [self.model, self.fallback_model] if self.fallback_model != self.model else [self.model]
        for model in models:
            body["model"] = model
            for attempt in range(self.max_retries + 1):
                try:
                    response = self.session.post(GROQ_ENDPOINT, headers=headers, json=body, timeout=self.timeout)
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                        time.sleep(2**attempt)
                        continue
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    try:
                        return json.loads(content)
                    except Exception:
                        logger.warning("Failed to parse GROQ model output as JSON; raw content: %s", content)
                        return None
                except Exception as exc:
                    if attempt < self.max_retries:
                        time.sleep(2**attempt)
                        continue
                    logger.warning("GROQ call failed key=%s model=%s: %s", cache_key, model, exc)
                    break
        return None

    def _compact_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        links = []
        for link in payload.get("links", [])[:20]:
            if not isinstance(link, dict):
                continue
            links.append(
                {
                    "text": clean_text(str(link.get("text", "")), 80),
                    "href": clean_text(str(link.get("href", "")), 220),
                }
            )
        return {
            "source_url": clean_text(str(payload.get("source_url", "")), 240),
            "container_path": clean_text(str(payload.get("container_path", "")), 180),
            "heading": clean_text(str(payload.get("heading", "")), 120),
            "text": clean_text(str(payload.get("text", "")), 2200),
            "links": links,
            "traditional": payload.get("traditional", {}),
            "dom_signals": payload.get("dom_signals", {}),
        }

    def _normalize_entity_response(self, response: dict[str, Any], source_url: str) -> dict[str, Any]:
        company_name = clean_text(self._string(response.get("company_name")), 120)
        emails = [clean_text(self._string(email)).lower() for email in self._as_list(response.get("emails")) if is_valid_email(self._string(email))]
        phones = [clean_text(self._string(phone), 32) for phone in self._as_list(response.get("phones")) if clean_text(self._string(phone))]
        social_links = [normalize_url(self._string(url), source_url) for url in self._as_list(response.get("social_links")) if self._string(url).strip()]
        quotes = self._as_list(response.get("quotes")) if self.quote_enabled else []
        normalized_quotes: list[dict[str, Any]] = []
        for quote in quotes:
            if not isinstance(quote, dict):
                continue
            normalized_quotes.append(
                {
                    "company": company_name,
                    "title": clean_text(self._string(quote.get("title")), 120),
                    "price": clean_text(self._string(quote.get("price")), 80),
                    "currency": clean_text(self._string(quote.get("currency")), 12),
                    "description": clean_text(self._string(quote.get("description")), 300),
                    "source_url": source_url,
                    "confidence": self._float_score(quote.get("confidence", 0)),
                    "extraction_scope": "ai_container",
                }
            )
        return {
            "company_name": company_name if has_real_entity_name(company_name) else "",
            "emails": unique_keep_order(emails),
            "phones": unique_keep_order(phones),
            "address": clean_text(self._string(response.get("address")), 240),
            "website": normalize_url(self._string(response.get("website")), source_url),
            "social_links": unique_keep_order(social_links),
            "confidence": self._float_score(response.get("confidence", 0)),
            "page_type": clean_text(self._string(response.get("page_type")), 80),
            "quotes": [quote for quote in normalized_quotes if quote.get("price")],
        }

    def _string(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    def _as_list(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]

    def _float_score(self, value: Any) -> float:
        try:
            return round(max(0.0, min(1.0, float(value))), 3)
        except (TypeError, ValueError):
            return 0.0

    def _cache_key(self, prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{prefix}-{digest}.json"

    def _read_cache(self, cache_key: str) -> dict[str, Any] | None:
        path = self.cache_dir / cache_key
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            (self.cache_dir / cache_key).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.debug("GROQ cache write failed: %s", exc)
