"""Confidence scoring for entity and quote extraction."""

from __future__ import annotations


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def entity_confidence(entity: dict, signals: dict | None = None) -> float:
    signals = signals or {}
    score = 0.0
    if entity.get("company_name"):
        score += 0.24
    if entity.get("email"):
        score += 0.18
    if entity.get("phone"):
        score += 0.16
    if entity.get("address"):
        score += 0.13
    if entity.get("website"):
        score += 0.12
    if entity.get("socials"):
        score += 0.07
    if signals.get("same_dom_block"):
        score += 0.18
    if signals.get("header_proximity"):
        score += 0.04
    if signals.get("semantic_similarity"):
        score += 0.06
    if signals.get("ai_confidence"):
        score += min(0.16, float(signals["ai_confidence"]) * 0.16)
    if signals.get("structured_data"):
        score += 0.08
    if signals.get("fallback_page"):
        score -= 0.12
    return clamp_score(score)


def quote_confidence(quote: dict, signals: dict | None = None) -> float:
    signals = signals or {}
    score = 0.0
    if quote.get("price"):
        score += 0.32
    if quote.get("currency"):
        score += 0.18
    if quote.get("title"):
        score += 0.16
    if quote.get("description"):
        score += 0.11
    if quote.get("company"):
        score += 0.1
    if signals.get("pricing_container"):
        score += 0.18
    if signals.get("starting_from"):
        score += 0.05
    return clamp_score(score)
