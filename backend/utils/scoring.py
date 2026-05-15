"""Confidence scoring helpers."""

from __future__ import annotations

from typing import Optional


def clamp_score(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return round(value, 4)


def score_presence(value: Optional[str], base: float = 0.4) -> float:
    if not value:
        return 0.0
    return clamp_score(base)


def score_confidence(method: str, boost: float = 0.0) -> float:
    base_scores = {
        "mailto": 0.9,
        "regex": 0.6,
        "script": 0.7,
        "base64": 0.7,
        "cloudflare": 0.85,
        "jsonld": 0.85,
        "tel": 0.85,
        "whatsapp": 0.7,
        "dom": 0.6,
        "heading": 0.75,
        "fallback": 0.4,
    }
    score = base_scores.get(method, 0.5) + boost
    return clamp_score(score)
