"""Shared extractor data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from bs4.element import Tag


@dataclass
class ExtractedValue:
    value: str
    confidence: float
    source: str
    element: Optional[Tag] = None
