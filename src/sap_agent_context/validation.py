"""Validation rules for SAP Agent Context items."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

from sap_agent_context.model import (
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

ALLOWED_SOURCE_SPECIFICITY = {"root_pointer", "exact_page", "catalog_entry", "internal_pattern"}
HIGH_SOURCE_SPECIFICITY = {"exact", "high"}


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
        _validate_kind_detail(issues, item)

        if item.data.get("access") == "gated" and item.data.get("requires_login") is not True:
            issues.append(_issue(path, item_id, "gated sources must set requires_login: true"))
    _validate_cross_item_evidence(issues, items)
    _validate_cross_item_relations(issues, items)
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
    for field in ["valid_from", "review_after", "expires_at", "retrieved_at"]:
        if field not in freshness:
            issues.append(_issue(str(item.path), item.item_id, f"freshness.{field} is required"))
            continue
        parsed = _parse_date(freshness[field])
        if parsed is None:
            issues.append(
                _issue(str(item.path), item.item_id, f"freshness.{field} must be YYYY-MM-DD")
            )
    valid_from = _parse_date(freshness.get("valid_from"))
    review_after = _parse_date(freshness.get("review_after"))
    expires_at = _parse_date(freshness.get("expires_at"))
    if valid_from and review_after and review_after < valid_from:
        issues.append(
            _issue(str(item.path), item.item_id, "freshness.review_after is before valid_from")
        )
    if review_after and expires_at and expires_at < review_after:
        issues.append(
            _issue(str(item.path), item.item_id, "freshness.expires_at is before review_after")
        )
    if review_after and review_after < today:
        issues.append(
            ValidationIssue(
                path=str(item.path),
                item_id=item.item_id,
                severity="warning",
                message=f"review_after is stale: {review_after.isoformat()}",
            )
        )
    if expires_at and expires_at < today:
        issues.append(
            ValidationIssue(
                path=str(item.path),
                item_id=item.item_id,
                severity="warning",
                message=f"expires_at is expired: {expires_at.isoformat()}",
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
    source_kind = str(source.get("kind") or "")
    expected_by_access = {
        "public": {"public_url"},
        "gated": {"gated_url"},
        "internal_derived": {"internal_pattern", "derived_summary"},
    }
    allowed = expected_by_access.get(str(item.data.get("access") or ""), set())
    if allowed and source_kind not in allowed:
        issues.append(
            _issue(
                str(item.path),
                item.item_id,
                f"source.kind {source_kind!r} does not match access {item.access!r}",
            )
        )
    specificity = source.get("specificity")
    if specificity is not None and specificity not in ALLOWED_SOURCE_SPECIFICITY:
        issues.append(
            _issue(
                str(item.path),
                item.item_id,
                f"source.specificity must be one of {sorted(ALLOWED_SOURCE_SPECIFICITY)}",
            )
        )
    required_specificity = str(item.data.get("requires_source_specificity") or "")
    if (
        required_specificity in HIGH_SOURCE_SPECIFICITY
        and _source_specificity(source) == "root_pointer"
    ):
        issues.append(
            _issue(
                str(item.path),
                item.item_id,
                (
                    "requires_source_specificity: high cannot be satisfied by a "
                    "generic root source URL"
                ),
            )
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
        elif len(str(claim.get("statement") or "").split()) < 9:
            issues.append(
                _issue(str(item.path), item.item_id, f"claims[{index}].statement is too vague")
            )
        evidence = claim.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            issues.append(
                _issue(str(item.path), item.item_id, f"claims[{index}].evidence is required")
            )


def _validate_kind_detail(issues: list[ValidationIssue], item: KnowledgeItem) -> None:
    relations = item.data.get("relations") if isinstance(item.data.get("relations"), dict) else {}
    if item.kind == "test_pattern":
        scenarios = item.data.get("test_scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            issues.append(_issue(str(item.path), item.item_id, "test_pattern needs test_scenarios"))
    if item.kind == "field_map":
        field_map = item.data.get("field_map")
        fields = relations.get("fields") if isinstance(relations, dict) else []
        if not isinstance(field_map, list) and not fields:
            issues.append(_issue(str(item.path), item.item_id, "field_map needs fields"))
    if item.kind == "sap_field":
        field_definitions = item.data.get("field_definitions")
        if not isinstance(field_definitions, list) or not field_definitions:
            issues.append(
                _issue(str(item.path), item.item_id, "sap_field needs field_definitions")
            )
    if item.kind == "decision_rule":
        rules = item.data.get("rules")
        if not isinstance(rules, list) or not rules:
            issues.append(_issue(str(item.path), item.item_id, "decision_rule needs rules"))


def _validate_cross_item_evidence(
    issues: list[ValidationIssue],
    items: list[KnowledgeItem],
) -> None:
    access_by_id = {item.item_id: item.access for item in items}
    for item in items:
        claims = item.data.get("claims")
        if not isinstance(claims, list):
            continue
        for claim_index, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict):
                continue
            evidence = claim.get("evidence")
            if not isinstance(evidence, list):
                continue
            for evidence_id in evidence:
                evidence_ref = str(evidence_id)
                if _is_url_evidence(evidence_ref):
                    continue
                evidence_access = access_by_id.get(evidence_ref)
                if evidence_access is None:
                    issues.append(
                        _issue(
                            str(item.path),
                            item.item_id,
                            (
                                f"claims[{claim_index}] evidence {evidence_ref!r} "
                                "is not a known item id or URL"
                            ),
                        )
                    )
                    continue
                if item.access == "public" and evidence_access == "internal_derived":
                    issues.append(
                        _issue(
                            str(item.path),
                            item.item_id,
                            (
                                f"claims[{claim_index}] public item uses internal-derived "
                                f"evidence {evidence_id!r}"
                            ),
                        )
                    )


def _validate_cross_item_relations(
    issues: list[ValidationIssue],
    items: list[KnowledgeItem],
) -> None:
    item_ids = {item.item_id for item in items}
    for item in items:
        raw_relations = item.data.get("relations")
        relations: dict[str, Any] = raw_relations if isinstance(raw_relations, dict) else {}
        for relation_name, relation_values in relations.items():
            if not isinstance(relation_values, list):
                continue
            for relation_value in relation_values:
                relation_ref = str(relation_value)
                if relation_ref.startswith("sap.") and relation_ref not in item_ids:
                    issues.append(
                        _issue(
                            str(item.path),
                            item.item_id,
                            f"relations.{relation_name} references missing item {relation_ref!r}",
                        )
                    )


def _is_url_evidence(value: str) -> bool:
    return value.startswith(("https://", "http://"))


def _source_specificity(source: dict[str, Any]) -> str:
    explicit = source.get("specificity")
    if explicit in ALLOWED_SOURCE_SPECIFICITY:
        return str(explicit)
    kind = str(source.get("kind") or "")
    if kind in {"internal_pattern", "derived_summary"}:
        return "internal_pattern"
    url = str(source.get("url") or "").rstrip("/")
    root_urls = {
        "https://help.sap.com/docs/SAP_S4HANA_CLOUD",
        "https://api.sap.com",
        "https://me.sap.com",
    }
    if url in root_urls:
        return "root_pointer"
    if url:
        return "exact_page"
    return "root_pointer"


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _issue(path: str, item_id: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=path, item_id=item_id, severity="error", message=message)
