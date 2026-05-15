"""Utility helpers for the CardosoX crawler system."""

from utils.cleaners import (
    clean_text,
    normalize_email,
    normalize_phone,
    normalize_address,
    normalize_url,
    normalize_social_url,
)
from utils.validators import (
    validate_urls,
    is_valid_url,
    is_valid_email,
    is_valid_phone,
    is_probable_company_link,
    is_social_link,
)
from utils.scoring import (
    clamp_score,
    score_confidence,
    score_presence,
)

__all__ = [
    "clean_text",
    "normalize_email",
    "normalize_phone",
    "normalize_address",
    "normalize_url",
    "normalize_social_url",
    "validate_urls",
    "is_valid_url",
    "is_valid_email",
    "is_valid_phone",
    "is_probable_company_link",
    "is_social_link",
    "clamp_score",
    "score_confidence",
    "score_presence",
]
