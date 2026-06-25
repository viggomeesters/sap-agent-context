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

    item_rows: list[sqlite3.Row] = []
    exact_item_rows: list[sqlite3.Row] = []
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
                (match_query, max(limit * 4, 20)),
            ).fetchall()
            exact_item_rows = _exact_item_rows(conn, exact_terms, max(limit * 4, 20))
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
                (match_query, max(limit * 2, 10)),
            ).fetchall()

    results = [_ranked(row, exact_terms) for row in [*item_rows, *exact_item_rows, *claim_rows]]
    if query_vector is not None:
        vector_hits = search_runtime_vectors(
            sqlite_path,
            query_vector=query_vector,
            limit=max(limit * 2, 10),
        )
        results.extend(_vector_ranked(hit) for hit in vector_hits)
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
        claim_results = [_ranked(row, exact_terms) for row in claim_rows]
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


def _ranked(row: sqlite3.Row, exact_terms: list[str]) -> dict[str, Any]:
    text = " ".join(str(row[key] or "") for key in ["id", "title", "text", "search_text"])
    haystack = text.lower()
    exact_hits = sum(1 for term in exact_terms if term.lower() in haystack)
    bm25_score = float(row["bm25_score"] or 0.0)
    source_boost = 100 if str(row["source"]).startswith("item_") else 0
    payload = _json_payload(str(row["payload_json"] or ""))
    return {
        "id": str(row["id"]),
        "title": str(row["title"]),
        "kind": str(row["kind"]),
        "text": str(row["text"]),
        "source": str(row["source"]),
        "exact_token_hits": exact_hits,
        "bm25_score": bm25_score,
        "score": exact_hits * 1000 + source_boost - bm25_score,
        "claim_ids": _claim_ids(row, payload),
        "source_ids": _source_ids(row, payload),
        "metadata": payload,
    }


def _vector_ranked(hit: dict[str, Any]) -> dict[str, Any]:
    metadata = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
    record_type = str(hit.get("record_type") or "")
    canonical_id = str(hit.get("canonical_record_id") or hit.get("id") or "")
    distance = float(hit.get("distance") or 0.0)
    result_id = str(hit.get("item_id") or hit.get("claim_id") or canonical_id)
    kind = str(metadata.get("kind") or record_type)
    return {
        "id": result_id,
        "title": str(metadata.get("title") or metadata.get("subject_id") or canonical_id),
        "kind": kind,
        "text": str(hit.get("text") or ""),
        "source": "vector",
        "exact_token_hits": 0,
        "bm25_score": 0.0,
        "vector_distance": distance,
        "score": 120 - distance,
        "claim_ids": [str(hit["claim_id"])] if hit.get("claim_id") else [],
        "source_ids": _strings(metadata.get("evidence_ids") or metadata.get("source_ids")),
        "metadata": metadata,
    }


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
    identifiers = IDENTIFIER_RE.findall(query)
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
