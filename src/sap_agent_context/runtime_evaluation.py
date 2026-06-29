"""Deterministic runtime retrieval fixture evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

DEFAULT_RUNTIME_FIXTURES = "schema/runtime-retrieval-fixtures.yaml"
DEFAULT_SQLITE = "build/context.sqlite"


def evaluate_runtime_retrieval(
    *,
    root: Path,
    sqlite_path: Path | None = None,
    fixtures_path: Path | None = None,
) -> dict[str, Any]:
    sqlite = sqlite_path or root / DEFAULT_SQLITE
    if not sqlite.exists():
        items = load_items(root)
        build_indexes(
            items,
            sqlite_path=sqlite,
            jsonl_path=root / "build/items.jsonl",
            vector_jsonl_path=root / "build/vector-corpus.jsonl",
            root=root,
        )
    fixtures = _load_fixtures(fixtures_path or root / DEFAULT_RUNTIME_FIXTURES)
    results = [_evaluate_fixture(sqlite, fixture) for fixture in fixtures]
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "status": "failed" if failures else "passed",
        "fixtures": len(results),
        "results": results,
    }


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"expected fixtures list in {path}")
    return [fixture for fixture in fixtures if isinstance(fixture, dict)]


def _evaluate_fixture(sqlite_path: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    filters = fixture.get("filters") if isinstance(fixture.get("filters"), dict) else {}
    results = search_runtime_index(
        sqlite_path,
        str(fixture.get("query") or ""),
        limit=int(fixture.get("limit") or 12),
        kind=filters.get("kind"),
        sap_product=filters.get("sap_product"),
        access=filters.get("access"),
        used_for=filters.get("used_for"),
        topic=filters.get("topic"),
    )
    failures = _fixture_failures(fixture, results)
    return {
        "id": str(fixture.get("id") or fixture.get("query") or "fixture"),
        "status": "failed" if failures else "passed",
        "top_ids": [str(result["id"]) for result in results[:5]],
        "failures": failures,
    }


def _fixture_failures(fixture: dict[str, Any], results: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    ids = [str(result["id"]) for result in results]
    top_ids = ids[: max(len(_strings(fixture.get("required_top_ids"))), 1)]
    for item_id in _strings(fixture.get("required_top_ids")):
        if item_id not in top_ids:
            failures.append(f"required top id missing: {item_id}; top={top_ids}")
    for item_id in _strings(fixture.get("required_ids")):
        if item_id not in ids:
            failures.append(f"required id missing: {item_id}; ids={ids}")
    for item_id in _strings(fixture.get("forbidden_ids")):
        if item_id in ids:
            failures.append(f"forbidden id present: {item_id}; ids={ids}")
    for item_id in _strings(fixture.get("forbidden_top_ids")):
        if item_id in top_ids:
            failures.append(f"forbidden top id present: {item_id}; top={top_ids}")
    top_kinds = [str(result.get("kind") or "") for result in results[: len(top_ids)]]
    for kind in _strings(fixture.get("forbidden_top_kinds")):
        if kind in top_kinds:
            failures.append(f"forbidden top kind present: {kind}; top_kinds={top_kinds}")
    if fixture.get("require_citations"):
        citeable = any(result.get("claim_ids") and result.get("source_ids") for result in results)
        if not citeable:
            failures.append("expected at least one result with claim_ids and source_ids")
    for rule in _mappings(fixture.get("must_rank_before")):
        higher = str(rule.get("higher") or "")
        lower = str(rule.get("lower") or "")
        if higher in ids and lower in ids and ids.index(higher) > ids.index(lower):
            failures.append(f"{higher} ranked after {lower}")
    return failures


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
