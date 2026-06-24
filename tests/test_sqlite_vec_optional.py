from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_build_index_reports_sqlite_vec_auto_skip_when_unavailable(tmp_path: Path) -> None:
    report = build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
        sqlite_vec="auto",
    )

    assert report["sqlite_vec"]["mode"] == "auto"
    assert report["sqlite_vec"]["status"] in {"enabled", "skipped"}
    assert report["sqlite_vec"]["status"] == "skipped"
    assert "unavailable" in report["sqlite_vec"]["reason"]
    with sqlite3.connect(tmp_path / "context.sqlite") as conn:
        row = conn.execute(
            "SELECT status, provider, dimension FROM vector_index_metadata"
        ).fetchone()
    assert row == ("skipped", "not-configured", 0)


def test_build_index_required_sqlite_vec_fails_clearly_when_unavailable(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="sqlite-vec is required but unavailable"):
        build_indexes(
            load_items(ROOT),
            sqlite_path=tmp_path / "context.sqlite",
            jsonl_path=tmp_path / "items.jsonl",
            vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
            root=ROOT,
            sqlite_vec="required",
        )


def test_vector_metadata_records_rebuildable_source_and_count(tmp_path: Path) -> None:
    report = build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
        sqlite_vec="off",
    )

    with sqlite3.connect(tmp_path / "context.sqlite") as conn:
        row = conn.execute(
            """
            SELECT status, source, content_hash_strategy, vector_records
            FROM vector_index_metadata
            """
        ).fetchone()
    assert row == ("off", "build/vector-corpus.jsonl", "stable vector record id + text", 1289)
    assert report["sqlite_vec"] == {"mode": "off", "status": "off", "reason": "disabled"}
