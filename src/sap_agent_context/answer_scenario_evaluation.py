"""Deterministic answer-scenario evaluation for SAP Agent Context.

This evaluates whether a user-style question retrieves enough source-labelled
context for an agent to answer safely. It does not call an LLM and does not
pretend to perform live web certification. Fixtures may include public web
check hints so agents can compare generated answers against external sources
when running a separate live-web review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

DEFAULT_ANSWER_SCENARIO_FIXTURES = "schema/answer-scenario-fixtures.yaml"
DEFAULT_SQLITE = "build/context.sqlite"


def evaluate_answer_scenarios(
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
    fixtures = _load_fixtures(fixtures_path or root / DEFAULT_ANSWER_SCENARIO_FIXTURES)
    results = [_evaluate_fixture(sqlite, fixture) for fixture in fixtures]
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "artifact_kind": "answer_scenario_evaluation_report",
        "status": "failed" if failures else "passed",
        "contract": {
            "purpose": (
                "prove user-style SAP questions retrieve enough source-labelled "
                "context for safe answers"
            ),
            "live_web_boundary": (
                "Fixtures can carry external evidence hints, but this deterministic gate "
                "does not claim live internet validation or expert certification."
            ),
            "answer_boundary": (
                "Retrieved context is answer evidence, not tenant/client-specific "
                "SAP configuration proof."
            ),
        },
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
        str(fixture.get("question") or fixture.get("query") or ""),
        limit=int(fixture.get("limit") or 12),
        kind=filters.get("kind"),
        sap_product=filters.get("sap_product"),
        access=filters.get("access"),
        used_for=filters.get("used_for"),
        topic=filters.get("topic"),
    )
    failures = _fixture_failures(fixture, results)
    top_ids = [str(result["id"]) for result in results[:5]]
    return {
        "id": str(fixture.get("id") or fixture.get("question") or "fixture"),
        "difficulty": str(fixture.get("difficulty") or "unspecified"),
        "question": str(fixture.get("question") or fixture.get("query") or ""),
        "expected_answer_status": str(fixture.get("expected_answer_status") or "ready"),
        "status": "failed" if failures else "passed",
        "top_ids": top_ids,
        "top_kinds": [str(result.get("kind") or "") for result in results[:5]],
        "citeable_results": sum(
            1 for result in results if result.get("claim_ids") and result.get("source_ids")
        ),
        "external_evidence_hints": _external_evidence_summary(fixture),
        "failures": failures,
    }


def _fixture_failures(fixture: dict[str, Any], results: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    ids = [str(result["id"]) for result in results]
    top_ids = ids[: max(len(_strings(fixture.get("required_top_ids"))), 1)]
    top_kinds = [str(result.get("kind") or "") for result in results[: len(top_ids)]]
    corpus = _result_corpus(results)
    corpus_by_id = {str(result["id"]): _result_text(result) for result in results}
    result_by_id = {str(result["id"]): result for result in results}

    if not results:
        failures.append("no retrieval results")

    required_ids = _strings(fixture.get("required_ids"))
    required_ids_top_n = _optional_positive_int(fixture.get("required_ids_top_n"))
    if required_ids_top_n is not None:
        required_window = set(ids[:required_ids_top_n])
        for item_id in required_ids:
            if item_id not in required_window:
                failures.append(
                    f"required id missing from top {required_ids_top_n}: {item_id}"
                )
    required_top_n_by_id = _mapping_of_positive_ints(fixture.get("required_top_n_by_id"))
    for item_id, top_n in required_top_n_by_id.items():
        if item_id not in set(ids[:top_n]):
            failures.append(f"required id missing from top {top_n}: {item_id}")

    for item_id in _strings(fixture.get("required_top_ids")):
        if item_id not in top_ids:
            failures.append(f"required top id missing: {item_id}; top={top_ids}")
    for item_id in required_ids:
        if item_id not in ids:
            failures.append(f"required id missing: {item_id}; ids={ids}")
    for item_id in _strings(fixture.get("forbidden_top_ids")):
        if item_id in top_ids:
            failures.append(f"forbidden top id present: {item_id}; top={top_ids}")
    for kind in _strings(fixture.get("forbidden_top_kinds")):
        if kind in top_kinds:
            failures.append(f"forbidden top kind present: {kind}; top_kinds={top_kinds}")

    for term in _strings(fixture.get("required_answer_terms")):
        if term.lower() not in corpus:
            failures.append(f"required answer term missing from retrieved context: {term}")

    required_terms_by_id = _mapping_of_string_lists(fixture.get("required_terms_by_id"))
    for item_id, terms in required_terms_by_id.items():
        item_corpus = corpus_by_id.get(item_id, "")
        if not item_corpus:
            failures.append(f"required_terms_by_id target not retrieved: {item_id}")
            continue
        for term in terms:
            if term.lower() not in item_corpus:
                failures.append(f"required term missing for {item_id}: {term}")

    if fixture.get("require_citations"):
        citeable = any(result.get("claim_ids") and result.get("source_ids") for result in results)
        if not citeable:
            failures.append("expected at least one result with claim_ids and source_ids")

    if fixture.get("require_citations_for_required_ids"):
        for item_id in required_ids:
            result = result_by_id.get(item_id)
            if not result:
                continue
            if not (result.get("claim_ids") and result.get("source_ids")):
                failures.append(f"required id is not citeable: {item_id}")

    if fixture.get("require_fail_closed_boundary"):
        boundary_terms = {"tenant", "client", "release", "verify", "evidence", "target"}
        if not boundary_terms & set(corpus.replace("-", " ").split()):
            failures.append(
                "expected tenant/client/release verification boundary in retrieved context"
            )

    expected_status = str(fixture.get("expected_answer_status") or "ready")
    if expected_status == "needs_curation" and not _strings(fixture.get("curation_reason")):
        failures.append("needs_curation scenarios must state curation_reason")

    evidence = _external_evidence(fixture)
    if evidence.get("required"):
        accepted_domains = _strings(evidence.get("accepted_domains"))
        search_terms = _strings(evidence.get("search_terms"))
        if not accepted_domains:
            failures.append("external_evidence.required needs accepted_domains")
        if not search_terms:
            failures.append("external_evidence.required needs search_terms")

    return failures


def _result_corpus(results: list[dict[str, Any]]) -> str:
    return " ".join(_result_text(result) for result in results)


def _result_text(result: dict[str, Any]) -> str:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    retrieval = _retrieval(metadata)
    parts = [
        str(result.get("id") or ""),
        str(result.get("title") or ""),
        str(result.get("text") or ""),
        str(metadata.get("summary") or ""),
        " ".join(_strings(metadata.get("topics"))),
        " ".join(_strings(metadata.get("used_for"))),
        " ".join(_strings(retrieval.get("keywords"))),
        " ".join(_strings(retrieval.get("queries"))),
    ]
    for field in metadata.get("field_definitions") or []:
        if isinstance(field, dict):
            parts.extend(
                str(field.get(key) or "")
                for key in ["key", "sap_structure", "sap_field", "description"]
            )
            labels = field.get("labels") if isinstance(field.get("labels"), dict) else {}
            for label in labels.values():
                if isinstance(label, dict):
                    parts.extend(str(value) for value in label.values())
    return " ".join(parts).lower()


def _external_evidence_summary(fixture: dict[str, Any]) -> dict[str, Any]:
    evidence = _external_evidence(fixture)
    return {
        "required": bool(evidence.get("required")),
        "mode": str(evidence.get("mode") or "offline_hint"),
        "accepted_domains": _strings(evidence.get("accepted_domains")),
        "search_terms": _strings(evidence.get("search_terms")),
    }


def _external_evidence(fixture: dict[str, Any]) -> dict[str, Any]:
    evidence = fixture.get("external_evidence")
    return evidence if isinstance(evidence, dict) else {}


def _retrieval(metadata: dict[str, Any]) -> dict[str, Any]:
    retrieval = metadata.get("retrieval")
    return retrieval if isinstance(retrieval, dict) else {}


def _mapping_of_string_lists(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, raw_terms in value.items():
        terms = _strings(raw_terms)
        if terms:
            result[str(key)] = terms
    return result


def _mapping_of_positive_ints(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw_number in value.items():
        number = _optional_positive_int(raw_number)
        if number is not None:
            result[str(key)] = number
    return result


def _optional_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
