"""Evaluate local embedding models against semantic NL/EN retrieval fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_embeddings import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    EmbedTexts,
    build_runtime_embeddings,
    embed_query,
)
from sap_agent_context.runtime_search import search_runtime_index

DEFAULT_SEMANTIC_FIXTURES = "schema/semantic-model-fixtures.yaml"
DEFAULT_SQLITE = "build/context.sqlite"
DEFAULT_ITEMS_JSONL = "build/items.jsonl"
DEFAULT_VECTOR_JSONL = "build/vector-corpus.jsonl"


def evaluate_semantic_models(
    *,
    root: Path,
    sqlite_path: Path | None = None,
    items_jsonl_path: Path | None = None,
    vector_jsonl_path: Path | None = None,
    fixtures_path: Path | None = None,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    models: list[str] | None = None,
    dimension: int = DEFAULT_EMBEDDING_DIMENSION,
    batch_size: int = 64,
    embed_texts: EmbedTexts | None = None,
) -> dict[str, Any]:
    """Run local semantic model evaluation without cloud/vector services."""
    if provider != DEFAULT_EMBEDDING_PROVIDER and embed_texts is None:
        raise ValueError("semantic model evaluation is local-only; only fastembed is implemented")
    model_names = models or [DEFAULT_EMBEDDING_MODEL]
    if not model_names:
        raise ValueError("at least one model is required")
    sqlite = sqlite_path or root / DEFAULT_SQLITE
    items_jsonl = items_jsonl_path or root / DEFAULT_ITEMS_JSONL
    vector_jsonl = vector_jsonl_path or root / DEFAULT_VECTOR_JSONL
    fixtures = _load_fixtures(fixtures_path or root / DEFAULT_SEMANTIC_FIXTURES)
    _build_runtime_index(root, sqlite, items_jsonl, vector_jsonl)

    model_results = [
        _evaluate_model(
            root=root,
            sqlite_path=sqlite,
            vector_jsonl_path=vector_jsonl,
            fixtures=fixtures,
            provider=provider,
            model=model,
            dimension=dimension,
            batch_size=batch_size,
            embed_texts=embed_texts,
        )
        for model in model_names
    ]
    recommended_default = _recommended_default(
        model_results,
        current_default=DEFAULT_EMBEDDING_MODEL,
    )
    failures = [failure for result in model_results for failure in result["failures"]]
    return {
        "status": "failed" if failures else "passed",
        "provider": provider,
        "default_model": DEFAULT_EMBEDDING_MODEL,
        "recommended_default": recommended_default,
        "fixtures": len(fixtures),
        "models": model_names,
        "results": model_results,
    }


def _build_runtime_index(root: Path, sqlite: Path, items_jsonl: Path, vector_jsonl: Path) -> None:
    items = load_items(root)
    build_indexes(
        items,
        sqlite_path=sqlite,
        jsonl_path=items_jsonl,
        vector_jsonl_path=vector_jsonl,
        root=root,
        sqlite_vec="required",
    )


def _evaluate_model(
    *,
    root: Path,
    sqlite_path: Path,
    vector_jsonl_path: Path,
    fixtures: list[dict[str, Any]],
    provider: str,
    model: str,
    dimension: int,
    batch_size: int,
    embed_texts: EmbedTexts | None,
) -> dict[str, Any]:
    build_payload = build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_jsonl_path,
        provider=provider,
        model=model,
        dimension=dimension,
        batch_size=batch_size,
        embed_texts=embed_texts,
    )
    fixture_results = [
        _evaluate_fixture(
            sqlite_path=sqlite_path,
            fixture=fixture,
            provider=provider,
            model=model,
            embed_texts=embed_texts,
        )
        for fixture in fixtures
    ]
    failures = [failure for result in fixture_results for failure in result["failures"]]
    passed = sum(1 for result in fixture_results if result["status"] == "passed")
    return {
        "status": "failed" if failures else "passed",
        "model": model,
        "dimension": build_payload["dimension"],
        "vector_records": build_payload["vector_records"],
        "passed": passed,
        "failed": len(fixture_results) - passed,
        "failures": failures,
        "fixtures": fixture_results,
    }


def _evaluate_fixture(
    *,
    sqlite_path: Path,
    fixture: dict[str, Any],
    provider: str,
    model: str,
    embed_texts: EmbedTexts | None,
) -> dict[str, Any]:
    query = str(fixture.get("query") or "")
    query_vector = _query_vector(query, provider=provider, model=model, embed_texts=embed_texts)
    filters = fixture.get("filters") if isinstance(fixture.get("filters"), dict) else {}
    results = search_runtime_index(
        sqlite_path,
        "",
        limit=int(fixture.get("limit") or 20),
        kind=filters.get("kind"),
        sap_product=filters.get("sap_product"),
        access=filters.get("access"),
        used_for=filters.get("used_for"),
        topic=filters.get("topic"),
        query_vector=query_vector,
    )
    failures = _fixture_failures(fixture, results)
    return {
        "id": str(fixture.get("id") or query),
        "language": str(fixture.get("language") or "unknown"),
        "query": query,
        "status": "failed" if failures else "passed",
        "top_ids": [str(result["id"]) for result in results[:5]],
        "top_sources": [str(result["source"]) for result in results[:5]],
        "failures": failures,
    }


def _query_vector(
    query: str,
    *,
    provider: str,
    model: str,
    embed_texts: EmbedTexts | None,
) -> list[float]:
    if embed_texts is not None:
        vectors = embed_texts([f"query: {query}"])
        if len(vectors) != 1:
            raise RuntimeError("embedding provider returned a mismatched query vector count")
        return vectors[0]
    return embed_query(query, provider=provider, model=model)


def _fixture_failures(fixture: dict[str, Any], results: list[dict[str, Any]]) -> list[str]:
    ids = [str(result["id"]) for result in results]
    failures: list[str] = []
    top_ids = ids[: max(len(_strings(fixture.get("required_top_ids"))), 1)]
    for item_id in _strings(fixture.get("required_top_ids")):
        if item_id not in top_ids:
            failures.append(
                f"{fixture.get('id')}: required top id missing: {item_id}; top={top_ids}"
            )
    for item_id in _strings(fixture.get("required_ids")):
        if item_id not in ids:
            failures.append(f"{fixture.get('id')}: required id missing: {item_id}; ids={ids}")
    for any_group in _list_of_strings(fixture.get("required_any")):
        if not any(item_id in ids for item_id in any_group):
            failures.append(
                f"{fixture.get('id')}: required any group missing: {any_group}; ids={ids}"
            )
    if fixture.get("require_vector_candidate") and not any(
        result.get("source") == "vector" for result in results
    ):
        failures.append(f"{fixture.get('id')}: expected at least one vector candidate")
    return failures


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"expected fixtures list in {path}")
    return [fixture for fixture in fixtures if isinstance(fixture, dict)]


def _recommended_default(results: list[dict[str, Any]], *, current_default: str) -> str:
    if not results:
        return current_default
    current = next((result for result in results if result["model"] == current_default), None)
    best = max(results, key=lambda result: (result["passed"], -result["failed"]))
    if current is None:
        return str(best["model"])
    if best["passed"] > current["passed"] and best["failed"] < current["failed"]:
        return str(best["model"])
    return current_default


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _list_of_strings(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    groups: list[list[str]] = []
    for item in value:
        group = _strings(item)
        if group:
            groups.append(group)
    return groups
