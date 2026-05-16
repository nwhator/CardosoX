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
        if self._has_conflicting_listing_fields(left, right):
            return False

        same_website = (
            left.get("website")
            and right.get("website")
            and domain_from_url(left["website"]) == domain_from_url(right["website"])
        )
        name_similarity = self.similarity(left.get("company_name"), right.get("company_name"))
        if same_website and name_similarity >= 0.72:
            return True
        if name_similarity >= 0.94 and self._one_side_is_sparse(left, right):
            return True
        return False

    def _has_conflicting_listing_fields(self, left: dict, right: dict) -> bool:
        """Avoid merging separate branches/listings into one entity bucket."""
        for key in ("phone", "address"):
            if left.get(key) and right.get(key) and left.get(key) != right.get(key):
                return True
        left_socials = set(left.get("socials") or [])
        right_socials = set(right.get("socials") or [])
        if left_socials and right_socials and left_socials.isdisjoint(right_socials):
            return True
        return False

    def _one_side_is_sparse(self, left: dict, right: dict) -> bool:
        fields = ("email", "phone", "address", "website")
        left_count = sum(bool(left.get(field)) for field in fields)
        right_count = sum(bool(right.get(field)) for field in fields)
        return left_count <= 1 or right_count <= 1

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
        for key in ("business_name", "listing_name"):
            if not target.get(key):
                target[key] = target.get("company_name") or source.get(key)
        if not target.get("extraction_scope") and source.get("extraction_scope"):
            target["extraction_scope"] = source["extraction_scope"]

        target["emails"] = unique_keep_order([*(target.get("emails") or []), *(source.get("emails") or [])])
        target["phone_numbers"] = unique_keep_order([*(target.get("phone_numbers") or []), *(source.get("phone_numbers") or [])])
        target["addresses"] = unique_keep_order([*(target.get("addresses") or []), *(source.get("addresses") or [])])
        target["socials"] = unique_keep_order([*(target.get("socials") or []), *(source.get("socials") or [])])
        target["confidence"] = clamp_score(max(target.get("confidence", 0), source.get("confidence", 0)) + 0.05)
