"""Completeness audit for SAP Agent Context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from sap_fo_knowledge_base.bundle import build_context_bundle
from sap_fo_knowledge_base.model import KnowledgeItem
from sap_fo_knowledge_base.validation import has_errors, validate_items

DEFAULT_MATRIX = "schema/completeness-matrix.yaml"


@dataclass(frozen=True)
class CompletenessFinding:
    severity: str
    area: str
    message: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "area": self.area,
            "message": self.message,
            "evidence": self.evidence,
        }


def audit_completeness(
    items: list[KnowledgeItem],
    *,
    root: Path,
    matrix_path: Path | None = None,
    current_date: date | None = None,
) -> dict[str, Any]:
    matrix = _load_matrix(matrix_path or root / DEFAULT_MATRIX)
    findings: list[CompletenessFinding] = []
    today = current_date or date.today()

    validation_issues = validate_items(items, current_date=today)
    if has_errors(validation_issues):
        findings.append(
            CompletenessFinding(
                severity="critical",
                area="validation",
                message="Schema validation has errors.",
                evidence=f"{len(validation_issues)} validation issues",
            )
        )

    _audit_minimums(findings, items, matrix)
    _audit_domains(findings, items, matrix)
    _audit_representative_queries(findings, items, root, matrix)

    critical = [finding for finding in findings if finding.severity == "critical"]
    important = [finding for finding in findings if finding.severity == "important"]
    later = [finding for finding in findings if finding.severity == "later"]
    return {
        "status": "passed" if not critical and not important else "failed",
        "scope": matrix.get("scope", {}),
        "items": len(items),
        "critical": len(critical),
        "important": len(important),
        "later": len(later),
        "findings": [finding.to_dict() for finding in findings],
    }


def _load_matrix(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return payload


def _audit_minimums(
    findings: list[CompletenessFinding],
    items: list[KnowledgeItem],
    matrix: dict[str, Any],
) -> None:
    raw_minimums = matrix.get("minimums")
    minimums: dict[str, Any] = raw_minimums if isinstance(raw_minimums, dict) else {}
    min_items = int(minimums.get("items_total") or 0)
    if len(items) < min_items:
        findings.append(
            CompletenessFinding(
                severity="critical",
                area="coverage",
                message=f"Knowledge base has fewer than {min_items} items.",
                evidence=f"items={len(items)}",
            )
        )

    required_kinds = set(_strings(minimums.get("required_kinds")))
    present_kinds = {item.kind for item in items}
    for missing in sorted(required_kinds - present_kinds):
        findings.append(
            CompletenessFinding(
                severity="critical",
                area="coverage",
                message=f"Missing required knowledge kind: {missing}",
                evidence=f"present={sorted(present_kinds)}",
            )
        )

    required_access = set(_strings(minimums.get("required_access_classes")))
    present_access = {item.access for item in items}
    for missing in sorted(required_access - present_access):
        findings.append(
            CompletenessFinding(
                severity="important",
                area="governance",
                message=f"Missing required access class: {missing}",
                evidence=f"present={sorted(present_access)}",
            )
        )


def _audit_domains(
    findings: list[CompletenessFinding],
    items: list[KnowledgeItem],
    matrix: dict[str, Any],
) -> None:
    raw_domains = matrix.get("domains")
    domains = raw_domains if isinstance(raw_domains, list) else []
    for domain in domains:
        if not isinstance(domain, dict):
            continue
        domain_id = str(domain.get("id") or "")
        topic_tokens = set(_strings(domain.get("topic_tokens")))
        domain_items = [
            item for item in items if topic_tokens.intersection(_normalized_tokens(item.topics))
        ]
        min_items = int(domain.get("min_items") or 0)
        if len(domain_items) < min_items:
            findings.append(
                CompletenessFinding(
                    severity="important",
                    area=f"domain:{domain_id}",
                    message=f"Domain has fewer than {min_items} matching items.",
                    evidence=f"items={len(domain_items)} tokens={sorted(topic_tokens)}",
                )
            )
        present_kinds = {item.kind for item in domain_items}
        for missing in sorted(set(_strings(domain.get("required_kinds"))) - present_kinds):
            findings.append(
                CompletenessFinding(
                    severity="important",
                    area=f"domain:{domain_id}",
                    message=f"Domain missing required kind: {missing}",
                    evidence=f"present={sorted(present_kinds)}",
                )
            )


def _audit_representative_queries(
    findings: list[CompletenessFinding],
    items: list[KnowledgeItem],
    root: Path,
    matrix: dict[str, Any],
) -> None:
    raw_queries = matrix.get("representative_queries")
    queries = raw_queries if isinstance(raw_queries, list) else []
    for query in queries:
        if not isinstance(query, dict):
            continue
        bundle = build_context_bundle(
            items,
            root=root,
            intent=str(query.get("intent") or ""),
            topic=str(query.get("topic") or ""),
            sap_product=str(query.get("sap_product") or ""),
            limit=int(query.get("limit") or 12),
        )
        query_id = str(query.get("id") or query.get("topic") or "query")
        if bundle.get("status") != "ready":
            findings.append(
                CompletenessFinding(
                    severity="critical",
                    area=f"query:{query_id}",
                    message="Representative query did not produce a ready bundle.",
                    evidence=str(bundle.get("status")),
                )
            )
            continue
        if bundle.get("gaps"):
            findings.append(
                CompletenessFinding(
                    severity="important",
                    area=f"query:{query_id}",
                    message="Representative bundle contains gaps.",
                    evidence="; ".join(str(gap) for gap in bundle["gaps"]),
                )
            )
        present_kinds = {str(item.get("kind")) for item in bundle.get("items", [])}
        for missing in sorted(set(_strings(query.get("required_kinds"))) - present_kinds):
            findings.append(
                CompletenessFinding(
                    severity="important",
                    area=f"query:{query_id}",
                    message=f"Representative bundle missing kind: {missing}",
                    evidence=f"present={sorted(present_kinds)}",
                )
            )
        for missing in _missing_quality_dimensions(
            bundle,
            required_dimensions=_strings(query.get("required_dimensions")),
        ):
            findings.append(
                CompletenessFinding(
                    severity="important",
                    area=f"query:{query_id}",
                    message=f"Representative bundle missing quality dimension: {missing}",
                    evidence=f"required={_strings(query.get('required_dimensions'))}",
                )
            )


def _normalized_tokens(values: list[str]) -> set[str]:
    tokens = set()
    for value in values:
        tokens.update(part for part in value.lower().replace("_", "-").split("-") if part)
        tokens.add(value.lower())
    return tokens


def _missing_quality_dimensions(
    bundle: dict[str, Any],
    *,
    required_dimensions: list[str],
) -> list[str]:
    return [
        dimension
        for dimension in required_dimensions
        if not _quality_dimension_present(bundle, dimension)
    ]


def _quality_dimension_present(bundle: dict[str, Any], dimension: str) -> bool:
    raw_items = bundle.get("items")
    items: list[dict[str, Any]] = raw_items if isinstance(raw_items, list) else []
    raw_citations = bundle.get("citations")
    citations: list[dict[str, Any]] = raw_citations if isinstance(raw_citations, list) else []
    kinds = {str(item.get("kind") or "") for item in items}

    if dimension == "source_traceability":
        return any(str(citation.get("url") or "").strip() for citation in citations)
    if dimension == "configuration_app":
        return "sap_app" in kinds
    if dimension == "business_object":
        return "sap_object" in kinds
    if dimension == "field_mapping":
        return "field_map" in kinds
    if dimension == "process_flow":
        return any("fo.process_flow" in item.get("used_for", []) for item in items)
    if dimension == "decision_rule":
        return "decision_rule" in kinds
    if dimension == "test_coverage":
        return "test_pattern" in kinds
    if dimension == "authorization_role":
        return "sap_role" in kinds
    if dimension == "access_policy":
        return "access_policy" in kinds
    return False


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
