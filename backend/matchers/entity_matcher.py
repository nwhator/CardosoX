"""Entity matching and confidence scoring."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from bs4.element import Tag

from extractors.base import ExtractedValue
from utils.scoring import clamp_score

if TYPE_CHECKING:
    from extractors.entity_extractor import CompanyEntity


class EntityMatcher:
    def adjust_values(self, values: List[ExtractedValue], name_element: Optional[Tag]) -> List[ExtractedValue]:
        adjusted: List[ExtractedValue] = []
        for item in values:
            boost = self._dom_proximity_boost(name_element, item.element)
            item.confidence = clamp_score(item.confidence + boost)
            adjusted.append(item)
        return adjusted

    def finalize_entity(self, entity: CompanyEntity) -> CompanyEntity:
        scores = []
        if entity.name:
            scores.append(entity.name.confidence)
        scores.extend([item.confidence for item in entity.emails])
        scores.extend([item.confidence for item in entity.phones])
        if entity.address:
            scores.append(entity.address.confidence)
        if entity.website:
            scores.append(entity.website.confidence)
        if entity.social_links:
            scores.extend([item.confidence for item in entity.social_links])
        if scores:
            entity.confidence = clamp_score(sum(scores) / len(scores))
        else:
            entity.confidence = 0.0
        return entity

    def _dom_proximity_boost(self, name_element: Optional[Tag], field_element: Optional[Tag]) -> float:
        if not name_element or not field_element:
            return 0.0
        if name_element == field_element:
            return 0.05
        if name_element in field_element.parents or field_element in name_element.parents:
            return 0.15
        name_parents = list(name_element.parents)
        field_parents = list(field_element.parents)
        for i, parent in enumerate(name_parents):
            if parent in field_parents:
                distance = i + field_parents.index(parent)
                if distance <= 4:
                    return 0.12
                if distance <= 8:
                    return 0.08
        return 0.0
