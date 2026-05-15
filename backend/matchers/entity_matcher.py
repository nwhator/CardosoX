"""Entity matching and de-duplication."""

from __future__ import annotations

from difflib import SequenceMatcher

from utils.cleaners import domain_from_url, unique_keep_order
from utils.scoring import clamp_score


class EntityMatcher:
    def similarity(self, left: str | None, right: str | None) -> float:
        if not left or not right:
            return 0.0
        return SequenceMatcher(None, left.lower(), right.lower()).ratio()

    def should_merge(self, left: dict, right: dict) -> bool:
        if left.get("email") and right.get("email") and left["email"] == right["email"]:
            return True
        if left.get("phone") and right.get("phone") and left["phone"] == right["phone"]:
            return True
        if left.get("website") and right.get("website") and domain_from_url(left["website"]) == domain_from_url(right["website"]):
            return True
        return self.similarity(left.get("company_name"), right.get("company_name")) >= 0.88

    def merge_entities(self, entities: list[dict]) -> list[dict]:
        merged: list[dict] = []
        for entity in sorted(entities, key=lambda item: item.get("confidence", 0), reverse=True):
            target = next((item for item in merged if self.should_merge(item, entity)), None)
            if not target:
                merged.append(entity)
                continue
            self._merge_into(target, entity)
        return sorted(merged, key=lambda item: item.get("confidence", 0), reverse=True)

    def _merge_into(self, target: dict, source: dict) -> None:
        for key in ("company_name", "email", "phone", "address", "website", "source_url"):
            if not target.get(key) and source.get(key):
                target[key] = source[key]

        target["emails"] = unique_keep_order([*(target.get("emails") or []), *(source.get("emails") or [])])
        target["phone_numbers"] = unique_keep_order([*(target.get("phone_numbers") or []), *(source.get("phone_numbers") or [])])
        target["addresses"] = unique_keep_order([*(target.get("addresses") or []), *(source.get("addresses") or [])])
        target["socials"] = unique_keep_order([*(target.get("socials") or []), *(source.get("socials") or [])])
        target["confidence"] = clamp_score(max(target.get("confidence", 0), source.get("confidence", 0)) + 0.05)

