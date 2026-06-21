"""Validation rules for SAP FO knowledge items."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

from sap_fo_knowledge_base.model import (
    ALLOWED_ACCESS,
    ALLOWED_KINDS,
    ALLOWED_STATUS,
    KnowledgeItem,
)

REQUIRED_TOP_LEVEL = {
    "id",
    "title",
    "kind",
    "status",
    "access",
    "requires_login",
    "sap_product",
    "topics",
    "used_for",
    "summary",
    "freshness",
    "source",
    "claims",
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    item_id: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "item_id": self.item_id,
            "severity": self.severity,
            "message": self.message,
        }


def validate_items(
    items: list[KnowledgeItem],
    *,
    current_date: date | None = None,
) -> list[ValidationIssue]:
    """Return validation issues for all loaded items."""
    today = current_date or date.today()
    issues: list[ValidationIssue] = []
    ids = Counter(item.item_id for item in items if "id" in item.data)

    for item in items:
        path = str(item.path)
        item_id = str(item.data.get("id") or "<missing>")
        missing = sorted(REQUIRED_TOP_LEVEL - set(item.data))
        for field in missing:
            issues.append(_issue(path, item_id, f"missing required field: {field}"))

        if ids[item_id] > 1:
            issues.append(_issue(path, item_id, "duplicate id"))
        _validate_enum(issues, item, "kind", ALLOWED_KINDS)
        _validate_enum(issues, item, "status", ALLOWED_STATUS)
        _validate_enum(issues, item, "access", ALLOWED_ACCESS)
        _validate_bool(issues, item, "requires_login")
        _validate_non_empty_list(issues, item, "topics")
        _validate_non_empty_list(issues, item, "used_for")
        _validate_freshness(issues, item, today)
        _validate_source(issues, item)
        _validate_claims(issues, item)

        if item.data.get("access") == "gated" and item.data.get("requires_login") is not True:
            issues.append(_issue(path, item_id, "gated sources must set requires_login: true"))
    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def _validate_enum(
    issues: list[ValidationIssue],
    item: KnowledgeItem,
    field: str,
    allowed: set[str],
) -> None:
    value = item.data.get(field)
    if value not in allowed:
        issues.append(
            _issue(str(item.path), item.item_id, f"{field} must be one of {sorted(allowed)}")
        )


def _validate_bool(issues: list[ValidationIssue], item: KnowledgeItem, field: str) -> None:
    if not isinstance(item.data.get(field), bool):
        issues.append(_issue(str(item.path), item.item_id, f"{field} must be boolean"))


def _validate_non_empty_list(
    issues: list[ValidationIssue],
    item: KnowledgeItem,
    field: str,
) -> None:
    value = item.data.get(field)
    if not isinstance(value, list) or not value:
        issues.append(_issue(str(item.path), item.item_id, f"{field} must be a non-empty list"))
        return
    if any(not str(entry).strip() for entry in value):
        issues.append(_issue(str(item.path), item.item_id, f"{field} contains empty values"))


def _validate_freshness(
    issues: list[ValidationIssue],
    item: KnowledgeItem,
    today: date,
) -> None:
    freshness = item.data.get("freshness")
    if not isinstance(freshness, dict):
        issues.append(_issue(str(item.path), item.item_id, "freshness must be a mapping"))
        return
    for field in ["valid_from", "review_after", "retrieved_at"]:
        if field not in freshness:
            issues.append(_issue(str(item.path), item.item_id, f"freshness.{field} is required"))
            continue
        parsed = _parse_date(freshness[field])
        if parsed is None:
            issues.append(
                _issue(str(item.path), item.item_id, f"freshness.{field} must be YYYY-MM-DD")
            )
    review_after = _parse_date(freshness.get("review_after"))
    if review_after and review_after < today:
        issues.append(
            ValidationIssue(
                path=str(item.path),
                item_id=item.item_id,
                severity="warning",
                message=f"review_after is stale: {review_after.isoformat()}",
            )
        )


def _validate_source(issues: list[ValidationIssue], item: KnowledgeItem) -> None:
    source = item.data.get("source")
    if not isinstance(source, dict):
        issues.append(_issue(str(item.path), item.item_id, "source must be a mapping"))
        return
    for field in ["kind", "title", "retrieved_at", "license_note"]:
        if not str(source.get(field) or "").strip():
            issues.append(_issue(str(item.path), item.item_id, f"source.{field} is required"))
    if item.data.get("access") in {"public", "gated"} and not str(source.get("url") or "").strip():
        issues.append(
            _issue(str(item.path), item.item_id, "external source items require source.url")
        )


def _validate_claims(issues: list[ValidationIssue], item: KnowledgeItem) -> None:
    claims = item.data.get("claims")
    if not isinstance(claims, list) or not claims:
        issues.append(_issue(str(item.path), item.item_id, "claims must be a non-empty list"))
        return
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            issues.append(
                _issue(str(item.path), item.item_id, f"claims[{index}] must be a mapping")
            )
            continue
        if not str(claim.get("statement") or "").strip():
            issues.append(
                _issue(str(item.path), item.item_id, f"claims[{index}].statement is required")
            )
        evidence = claim.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            issues.append(
                _issue(str(item.path), item.item_id, f"claims[{index}].evidence is required")
            )


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _issue(path: str, item_id: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=path, item_id=item_id, severity="error", message=message)
