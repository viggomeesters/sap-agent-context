"""Deterministic FO output fixture evaluation for context bundles."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.model import KnowledgeItem

DEFAULT_FIXTURES = "schema/fo-output-evaluation-fixtures.yaml"


def evaluate_fo_output_fixtures(
    items: list[KnowledgeItem],
    *,
    root: Path,
    fixtures_path: Path | None = None,
    current_date: date | None = None,
) -> dict[str, Any]:
    fixtures = _load_fixtures(fixtures_path or root / DEFAULT_FIXTURES)
    results = [
        _evaluate_fixture(items, root=root, fixture=fixture, current_date=current_date)
        for fixture in fixtures
    ]
    failed = [result for result in results if result["status"] == "failed"]
    return {
        "status": "failed" if failed else "passed",
        "fixtures": len(results),
        "failed": len(failed),
        "results": results,
    }


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_fixtures = payload.get("fixtures")
    if not isinstance(raw_fixtures, list):
        raise ValueError(f"expected fixtures list in {path}")
    return [fixture for fixture in raw_fixtures if isinstance(fixture, dict)]


def _evaluate_fixture(
    items: list[KnowledgeItem],
    *,
    root: Path,
    fixture: dict[str, Any],
    current_date: date | None,
) -> dict[str, Any]:
    fixture_date = _fixture_date(fixture) or current_date
    bundle = build_context_bundle(
        items,
        root=root,
        intent=str(fixture.get("intent") or ""),
        topic=str(fixture.get("topic") or ""),
        sap_product=str(fixture.get("sap_product") or ""),
        limit=int(fixture.get("limit") or 12),
        current_date=fixture_date,
    )
    failures = _fixture_failures(fixture, bundle)
    return {
        "id": str(fixture.get("id") or fixture.get("topic") or "fixture"),
        "status": "failed" if failures else "passed",
        "bundle_status": bundle.get("status"),
        "failures": failures,
        "bundle_gaps": bundle.get("gaps", []),
    }


def _fixture_failures(fixture: dict[str, Any], bundle: dict[str, Any]) -> list[str]:
    failures = []
    bundle_items = bundle.get("items") if isinstance(bundle.get("items"), list) else []
    bundle_ids = {str(item.get("id") or "") for item in bundle_items}
    bundle_kinds = {str(item.get("kind") or "") for item in bundle_items}
    bundle_access = {str(item.get("access") or "") for item in bundle_items}
    bundle_fields = _bundle_fields(bundle_items)
    bundle_gaps = [str(gap) for gap in bundle.get("gaps", [])]

    expected_status = fixture.get("expected_status")
    if expected_status and bundle.get("status") != expected_status:
        failures.append(f"expected status {expected_status!r}, got {bundle.get('status')!r}")

    for item_id in _strings(fixture.get("required_item_ids")):
        if item_id not in bundle_ids:
            failures.append(f"missing required item {item_id!r}")
    for kind in _strings(fixture.get("required_kinds")):
        if kind not in bundle_kinds:
            failures.append(f"missing required kind {kind!r}")
    for field in _strings(fixture.get("required_fields")):
        if field not in bundle_fields:
            failures.append(f"missing required field {field!r}")
    for access in _strings(fixture.get("required_access_labels")):
        if access not in bundle_access:
            failures.append(f"missing required access label {access!r}")

    if fixture.get("require_source_traceability") and not _has_source_traceability(bundle):
        failures.append("missing source traceability citation URL")
    if fixture.get("require_open_questions") and not bundle_gaps:
        failures.append("expected gaps/open questions for consultant follow-up")
    expected_gap = str(fixture.get("expected_gap_contains") or "")
    if expected_gap and not any(expected_gap in gap for gap in bundle_gaps):
        failures.append(f"expected gap containing {expected_gap!r}")
    return failures


def _bundle_fields(bundle_items: list[dict[str, Any]]) -> set[str]:
    fields = set()
    for item in bundle_items:
        raw_relations = item.get("relations")
        relations: dict[str, Any] = raw_relations if isinstance(raw_relations, dict) else {}
        raw_fields = relations.get("fields")
        if isinstance(raw_fields, list):
            fields.update(str(field) for field in raw_fields)
    return fields


def _has_source_traceability(bundle: dict[str, Any]) -> bool:
    raw_citations = bundle.get("citations")
    citations: list[dict[str, Any]] = raw_citations if isinstance(raw_citations, list) else []
    return any(str(citation.get("url") or "").strip() for citation in citations)


def _fixture_date(fixture: dict[str, Any]) -> date | None:
    value = fixture.get("current_date")
    if not value:
        return None
    return date.fromisoformat(str(value))


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
