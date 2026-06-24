from __future__ import annotations

import sqlite3
from pathlib import Path

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

ROOT = Path(__file__).resolve().parents[1]


def _index_path(tmp_path: Path) -> Path:
    sqlite_path = tmp_path / "context.sqlite"
    build_indexes(
        load_items(ROOT),
        sqlite_path=sqlite_path,
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector.jsonl",
        root=ROOT,
    )
    return sqlite_path


def test_runtime_fts_exact_transaction_identifier_ranks_first(tmp_path: Path) -> None:
    results = search_runtime_index(_index_path(tmp_path), "IE03 display equipment", limit=5)

    assert results[0]["id"] == "sap.app.eam.pm.ie03"
    assert results[0]["exact_token_hits"] >= 1
    assert results[0]["source"].startswith("item_")


def test_runtime_fts_exact_table_and_field_identifiers_are_reliable(tmp_path: Path) -> None:
    sqlite_path = _index_path(tmp_path)

    equi_results = search_runtime_index(sqlite_path, "EQUI equipment table", limit=8)
    dd03vt_results = search_runtime_index(sqlite_path, "DD03VT field catalog", limit=8)

    assert any(
        result["id"] == "sap.field-set.ecc-anonymous-equi-dd03vt-field-catalog"
        for result in equi_results[:3]
    )
    assert any(
        result["id"] == "sap.field-set.ecc-anonymous-dd03vt-dd03vt-field-catalog"
        for result in dd03vt_results[:3]
    )


def test_runtime_fts_claims_are_searchable_with_evidence_context(tmp_path: Path) -> None:
    results = search_runtime_index(
        _index_path(tmp_path), "IE03 authorization screen layout universal", limit=10
    )

    assert any(result["source"] == "claim_fts" for result in results)
    assert any("IE03" in result["text"] or "ie03" in result["text"].lower() for result in results)


def test_runtime_fts_tables_include_claim_and_source_fts(tmp_path: Path) -> None:
    sqlite_path = _index_path(tmp_path)
    with sqlite3.connect(sqlite_path) as conn:
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
        tables = {row[0] for row in table_rows}

    assert {"item_fts", "claim_fts", "source_fts"} <= tables
