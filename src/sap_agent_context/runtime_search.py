"""Runtime SQLite/FTS retrieval helpers."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from sap_agent_context.runtime_embeddings import search_runtime_vectors

IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9_/-]{2,}\b")
WORD_RE = re.compile(r"[A-Za-z0-9_/-]+")
GENERIC_EXACT_TERMS = {"SAP"}


def search_runtime_index(
    sqlite_path: Path,
    query: str,
    *,
    limit: int = 12,
    kind: str | None = None,
    sap_product: str | None = None,
    access: str | None = None,
    used_for: str | None = None,
    topic: str | None = None,
    query_vector: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Search the generated runtime SQLite index.

    Exact SAP identifiers (transactions, tables, fields, scope ids) get a
    deterministic boost before BM25 so IE03/EQUI/DD03VT-style queries do not get
    demoted by vague semantic text. When a query vector is supplied and local
    embeddings are present, vector hits are merged as additional candidates.
    """
    tokens = _tokens(query)
    match_query = _fts_query(tokens)
    exact_terms = _exact_terms(query, tokens)
    if not match_query and query_vector is None:
        return []

    candidate_limit = max(limit * 10, 100)
    item_rows: list[sqlite3.Row] = []
    exact_item_rows: list[sqlite3.Row] = []
    focused_item_rows: list[sqlite3.Row] = []
    claim_rows: list[sqlite3.Row] = []
    if match_query:
        with sqlite3.connect(sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            item_rows = conn.execute(
                """
                SELECT
                  items.id,
                  items.title,
                  items.kind,
                  items.summary AS text,
                  'item_fts' AS source,
                  bm25(item_fts) AS bm25_score,
                  item_fts.retrieval_text AS search_text,
                  items.payload_json AS payload_json
                FROM item_fts
                JOIN items ON items.id = item_fts.id
                WHERE item_fts MATCH ?
                LIMIT ?
                """,
                (match_query, candidate_limit),
            ).fetchall()
            exact_item_rows = _exact_item_rows(conn, exact_terms, candidate_limit)
            focused_item_rows = [
                *_foundation_item_rows(conn, tokens),
                *_org_process_item_rows(conn, tokens),
                *_focused_item_rows(conn, tokens, max(limit * 2, 20)),
            ]
            claim_rows = conn.execute(
                """
                SELECT
                  claims.id,
                  claims.subject_id AS title,
                  'claim' AS kind,
                  claims.statement AS text,
                  'claim_fts' AS source,
                  bm25(claim_fts) AS bm25_score,
                  claim_fts.statement || ' ' || claim_fts.evidence_text AS search_text,
                  claims.payload_json AS payload_json
                FROM claim_fts
                JOIN claims ON claims.id = claim_fts.id
                WHERE claim_fts MATCH ?
                LIMIT ?
                """,
                (match_query, max(limit * 4, 40)),
            ).fetchall()

    results = [
        _ranked(row, tokens, exact_terms)
        for row in [*item_rows, *exact_item_rows, *focused_item_rows, *claim_rows]
    ]
    if query_vector is not None:
        vector_hits = search_runtime_vectors(
            sqlite_path,
            query_vector=query_vector,
            limit=max(limit * 2, 10),
        )
        results.extend(_vector_ranked(hit, tokens) for hit in vector_hits)
    filtered = [
        result
        for result in results
        if _passes_filters(
            result,
            kind=kind,
            sap_product=sap_product,
            access=access,
            used_for=used_for,
            topic=topic,
        )
    ]
    deduped = {result["id"]: result for result in sorted(filtered, key=lambda row: -row["score"])}
    ordered = sorted(
        deduped.values(), key=lambda row: (-row["score"], row["bm25_score"], row["id"])
    )
    selected = ordered[:limit]
    if claim_rows and not any(row["source"] == "claim_fts" for row in selected):
        claim_results = [_ranked(row, tokens, exact_terms) for row in claim_rows]
        best_claim = sorted(
            claim_results, key=lambda row: (-row["score"], row["bm25_score"], row["id"])
        )[0]
        selected = [*selected[: max(limit - 1, 0)], best_claim]
    return selected[:limit]


def _exact_item_rows(
    conn: sqlite3.Connection,
    exact_terms: list[str],
    limit: int,
) -> list[sqlite3.Row]:
    if not exact_terms:
        return []
    predicates = []
    params: list[str] = []
    for term in exact_terms:
        predicates.append(
            "(items.id LIKE ? OR items.title LIKE ? OR items.summary LIKE ? "
            "OR items.payload_json LIKE ?)"
        )
        like = f"%{term}%"
        params.extend([like, like, like, like])
    params.append(str(limit))
    return conn.execute(
        f"""
        SELECT
          items.id,
          items.title,
          items.kind,
          items.summary AS text,
          'item_exact' AS source,
          0.0 AS bm25_score,
          items.payload_json AS search_text,
          items.payload_json AS payload_json
        FROM items
        WHERE {' OR '.join(predicates)}
        LIMIT ?
        """,
        params,
    ).fetchall()


def _foundation_item_rows(
    conn: sqlite3.Connection,
    tokens: list[str],
) -> list[sqlite3.Row]:
    token_set = {token.lower() for token in tokens}
    if not _looks_like_foundation_query(token_set):
        return []
    preferred_ids = [
        "sap.object.sap-context-foundation",
        "sap.field-set.sap-context-lenses",
        "sap.rule.sap-answer-ontology-gate",
        "sap.fo-pattern.sap-from-zero-answer",
        "sap.test-pattern.sap-foundation-fail-closed",
    ]
    placeholders = ", ".join("?" for _ in preferred_ids)
    return conn.execute(
        f"""
        SELECT
          items.id,
          items.title,
          items.kind,
          items.summary AS text,
          'item_focus' AS source,
          0.0 AS bm25_score,
          items.payload_json AS search_text,
          items.payload_json AS payload_json
        FROM items
        WHERE items.id IN ({placeholders})
        ORDER BY CASE items.id
          WHEN 'sap.object.sap-context-foundation' THEN 0
          WHEN 'sap.field-set.sap-context-lenses' THEN 1
          WHEN 'sap.rule.sap-answer-ontology-gate' THEN 2
          WHEN 'sap.fo-pattern.sap-from-zero-answer' THEN 3
          WHEN 'sap.test-pattern.sap-foundation-fail-closed' THEN 4
          ELSE 5
        END
        """,
        preferred_ids,
    ).fetchall()


def _org_process_item_rows(
    conn: sqlite3.Connection,
    tokens: list[str],
) -> list[sqlite3.Row]:
    token_set = {token.lower() for token in tokens}
    if not _looks_like_org_process_query(token_set):
        return []
    preferred_ids = [
        "sap.rule.sap-org-process-evidence-gate",
        "sap.object.sap-org-model-lens",
        "sap.field-set.sap-process-lenses",
        "sap.fo-pattern.sap-org-process-discovery",
        "sap.test-pattern.sap-org-process-fail-closed",
        "sap.object.sap-org-company-code",
        "sap.object.sap-org-plant",
        "sap.object.sap-org-purchasing-organization",
        "sap.object.sap-org-sales-organization",
        "sap.object.sap-org-distribution-channel",
        "sap.object.sap-org-controlling-area",
        "sap.object.sap-org-storage-location",
        "sap.object.sap-org-business-partner-role",
    ]
    placeholders = ", ".join("?" for _ in preferred_ids)
    return conn.execute(
        f"""
        SELECT
          items.id,
          items.title,
          items.kind,
          items.summary AS text,
          'item_focus' AS source,
          0.0 AS bm25_score,
          items.payload_json AS search_text,
          items.payload_json AS payload_json
        FROM items
        WHERE items.id IN ({placeholders})
        """,
        preferred_ids,
    ).fetchall()


def _focused_item_rows(
    conn: sqlite3.Connection,
    tokens: list[str],
    limit: int,
) -> list[sqlite3.Row]:
    token_set = {token.lower() for token in tokens}
    if not ({"fo", "pattern", "decision", "rule", "fail", "closed"} & token_set):
        return []
    signal_terms = [
        token
        for token in tokens
        if len(token) >= 5 and token.lower() not in {"decision", "pattern"}
    ][:6]
    if len(signal_terms) < 3:
        return []
    predicates = ["items.payload_json LIKE ?" for _ in signal_terms]
    params = [f"%{term}%" for term in signal_terms]
    params.append(str(limit))
    return conn.execute(
        f"""
        SELECT
          items.id,
          items.title,
          items.kind,
          items.summary AS text,
          'item_focus' AS source,
          0.0 AS bm25_score,
          items.payload_json AS search_text,
          items.payload_json AS payload_json
        FROM items
        WHERE {' AND '.join(predicates)}
        LIMIT ?
        """,
        params,
    ).fetchall()


def _ranked(row: sqlite3.Row, tokens: list[str], exact_terms: list[str]) -> dict[str, Any]:
    text = " ".join(str(row[key] or "") for key in ["id", "title", "text", "search_text"])
    haystack = text.lower()
    exact_hits = sum(1 for term in exact_terms if term.lower() in haystack)
    bm25_score = float(row["bm25_score"] or 0.0)
    source = str(row["source"])
    source_boost = 100 if source.startswith("item_") else -200
    payload = _json_payload(str(row["payload_json"] or ""))
    kind = str(row["kind"])
    item_id = str(row["id"])
    focus_boost = _focus_boost(tokens, kind, item_id, payload)
    claim_ids = _claim_ids(row, payload)
    source_ids = _source_ids(row, payload)
    result = {
        "id": item_id,
        "title": str(row["title"]),
        "kind": kind,
        "text": str(row["text"]),
        "source": str(row["source"]),
        "exact_token_hits": exact_hits,
        "bm25_score": bm25_score,
        "focus_boost": focus_boost,
        "score": exact_hits * 1000 + source_boost + focus_boost - bm25_score,
        "claim_ids": claim_ids,
        "source_ids": source_ids,
        "metadata": payload,
    }
    result["explain"] = _explain_result(
        result,
        tokens=tokens,
        exact_terms=exact_terms,
        search_text=text,
    )
    return result


def _vector_ranked(hit: dict[str, Any], tokens: list[str]) -> dict[str, Any]:
    metadata = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
    record_type = str(hit.get("record_type") or "")
    canonical_id = str(hit.get("canonical_record_id") or hit.get("id") or "")
    distance = float(hit.get("distance") or 0.0)
    result_id = str(hit.get("item_id") or hit.get("claim_id") or canonical_id)
    kind = str(metadata.get("kind") or record_type)
    focus_boost = _focus_boost(tokens, kind, result_id, metadata)
    source_ids = _strings(metadata.get("evidence_ids") or metadata.get("source_ids"))
    result = {
        "id": result_id,
        "title": str(metadata.get("title") or metadata.get("subject_id") or canonical_id),
        "kind": kind,
        "text": str(hit.get("text") or ""),
        "source": "vector",
        "exact_token_hits": 0,
        "bm25_score": 0.0,
        "vector_distance": distance,
        "focus_boost": focus_boost,
        "score": 120 + focus_boost - distance,
        "claim_ids": [str(hit["claim_id"])] if hit.get("claim_id") else [],
        "source_ids": source_ids,
        "metadata": metadata,
    }
    result["explain"] = _explain_result(
        result,
        tokens=tokens,
        exact_terms=[],
        search_text=f"{hit.get('text') or ''} {json.dumps(metadata, sort_keys=True, default=str)}",
        vector_distance=distance,
        vector_model=str(hit.get("model") or metadata.get("model") or ""),
    )
    return result


def _explain_result(
    result: dict[str, Any],
    *,
    tokens: list[str],
    exact_terms: list[str],
    search_text: str,
    vector_distance: float | None = None,
    vector_model: str = "",
) -> dict[str, Any]:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    haystack = search_text.lower()
    matched_terms = [token for token in tokens if token.lower() in haystack]
    explain: dict[str, Any] = {
        "rank_source": result.get("source"),
        "score": result.get("score"),
        "matched_terms": _dedupe(matched_terms),
        "exact_terms": exact_terms,
        "exact_token_hits": result.get("exact_token_hits", 0),
        "bm25_score": result.get("bm25_score", 0.0),
        "focus_boost": result.get("focus_boost", 0.0),
        "access": metadata.get("access", ""),
        "freshness": metadata.get("freshness", {}),
        "source_ids": result.get("source_ids", []),
        "claim_ids": result.get("claim_ids", []),
    }
    if vector_distance is not None:
        explain["vector_distance"] = vector_distance
        explain["vector_model"] = vector_model
    return explain


def _focus_boost(
    tokens: list[str],
    kind: str,
    item_id: str,
    metadata: dict[str, Any],
) -> float:
    token_set = {token.lower() for token in tokens}
    topics = {topic.lower() for topic in _strings(metadata.get("topics"))}
    boost = 0.0
    if kind == "fo_pattern" and ({"fo", "pattern"} & token_set):
        boost += 45.0
    if kind == "decision_rule" and ({"decision", "rule", "fail", "closed"} & token_set):
        boost += 45.0
    if kind == "test_pattern" and ({"test", "scenario", "probe"} & token_set):
        boost += 30.0
    if item_id.startswith("sap.bulk.") and ({"fo", "pattern", "decision", "rule"} & token_set):
        boost -= 25.0
    if _looks_like_foundation_query(token_set):
        if item_id.startswith("sap.bulk."):
            boost -= 400.0
        if "sap-foundation" in topics or item_id in {
            "sap.object.sap-context-foundation",
            "sap.field-set.sap-context-lenses",
            "sap.rule.sap-answer-ontology-gate",
        }:
            boost += 1400.0
        if "context-ontology" in topics or "from-zero" in topics:
            boost += 250.0
        if kind in {"sap_object", "sap_field", "decision_rule"}:
            boost += 75.0
        if kind == "sap_app":
            boost -= 150.0
    if _looks_like_org_process_query(token_set):
        if item_id.startswith("sap.bulk."):
            boost -= 120.0
        if "org-process" in topics or "org-model" in topics or item_id in {
            "sap.rule.sap-org-process-evidence-gate",
            "sap.object.sap-org-model-lens",
            "sap.field-set.sap-process-lenses",
            "sap.fo-pattern.sap-org-process-discovery",
            "sap.test-pattern.sap-org-process-fail-closed",
        }:
            boost += 900.0
        if {"tenant", "configured"} & token_set and item_id in {
            "sap.rule.sap-org-process-evidence-gate",
            "sap.test-pattern.sap-org-process-fail-closed",
        }:
            boost += 450.0
        if {"company", "code"} <= token_set and item_id == "sap.object.sap-org-company-code":
            boost += 350.0
        if "plant" in token_set and item_id == "sap.object.sap-org-plant":
            boost += 350.0
        if (
            {"purchasing", "purchase"} & token_set
            and item_id == "sap.object.sap-org-purchasing-organization"
        ):
            boost += 350.0
        if (
            {"sales", "o2c"} & token_set
            and item_id == "sap.object.sap-org-sales-organization"
        ):
            boost += 250.0
        if (
            {"p2p", "o2c", "r2r", "h2r", "d2o"} & token_set
            and item_id == "sap.field-set.sap-process-lenses"
        ):
            boost += 350.0
        if kind in {
            "decision_rule",
            "sap_object",
            "sap_field",
            "fo_pattern",
            "test_pattern",
        }:
            boost += 80.0
        if kind == "sap_app":
            boost -= 120.0
    return boost


def _looks_like_foundation_query(token_set: set[str]) -> bool:
    explicit_foundation_intent = {
        "foundation",
        "from-zero",
        "ontology",
        "sap-context",
    }
    context_signals = {
        "sap",
        "lifecycle",
        "landscape",
        "customizing",
        "evidence",
        "source",
    }
    return bool(explicit_foundation_intent & token_set) and len(context_signals & token_set) >= 2


def _looks_like_org_process_query(token_set: set[str]) -> bool:
    org_signals = {
        "company",
        "code",
        "controlling",
        "area",
        "plant",
        "storage",
        "location",
        "sales",
        "distribution",
        "purchasing",
        "purchase",
        "partner",
    }
    process_signals = {
        "o2c",
        "p2p",
        "r2r",
        "h2r",
        "d2o",
        "process",
        "lens",
        "procure",
        "pay",
        "order",
        "cash",
        "versus",
        "vs",
        "compare",
    }
    explicit_org_question = bool({"org", "organization", "organisation"} & token_set) and bool(
        {"unit", "owns", "owner", *org_signals} & token_set
    )
    tenant_org_assertion = bool({"tenant", "configured"} & token_set) and bool(
        org_signals & token_set
    )
    process_question = bool(org_signals & token_set) and bool(process_signals & token_set)
    return explicit_org_question or tenant_org_assertion or process_question


def _json_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _claim_ids(row: sqlite3.Row, payload: dict[str, Any]) -> list[str]:
    if str(row["source"]) == "claim_fts":
        return [str(row["id"])]
    raw = payload.get("claim_ids")
    return [str(value) for value in raw] if isinstance(raw, list) else []


def _source_ids(row: sqlite3.Row, payload: dict[str, Any]) -> list[str]:
    if str(row["source"]) == "claim_fts":
        raw = payload.get("evidence_ids")
        return [str(value) for value in raw] if isinstance(raw, list) else []
    raw = payload.get("source_ids")
    return [str(value) for value in raw] if isinstance(raw, list) else []


def _passes_filters(
    result: dict[str, Any],
    *,
    kind: str | None,
    sap_product: str | None,
    access: str | None,
    used_for: str | None,
    topic: str | None,
) -> bool:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    if result["source"] == "claim_fts":
        return True
    if kind and metadata.get("kind") != kind:
        return False
    if sap_product and metadata.get("sap_product") != sap_product:
        return False
    if access and metadata.get("access") != access:
        return False
    if used_for and used_for not in _strings(metadata.get("used_for")):
        return False
    return not (topic and topic not in _strings(metadata.get("topics")))


def _tokens(query: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for token in WORD_RE.findall(query):
        cleaned = token.strip("-_/ ")
        if len(cleaned) < 2:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _exact_terms(query: str, tokens: list[str]) -> list[str]:
    identifiers = [
        identifier
        for identifier in IDENTIFIER_RE.findall(query)
        if identifier not in GENERIC_EXACT_TERMS
    ]
    short_exact = [token for token in tokens if any(char.isdigit() for char in token)]
    return _dedupe([*identifiers, *short_exact])


def _fts_query(tokens: list[str]) -> str:
    if not tokens:
        return ""
    return " OR ".join(_quote_fts(token) for token in tokens[:12])


def _quote_fts(token: str) -> str:
    return '"' + token.replace('"', '""') + '"'


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
