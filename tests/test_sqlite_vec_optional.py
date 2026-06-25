from __future__ import annotations

import sqlite3
from pathlib import Path

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_build_index_reports_sqlite_vec_auto_enabled_when_dependency_is_installed(
    tmp_path: Path,
) -> None:
    report = build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
        sqlite_vec="auto",
    )

    assert report["sqlite_vec"]["mode"] == "auto"
    assert report["sqlite_vec"]["status"] == "enabled"
    assert "import succeeded" in report["sqlite_vec"]["reason"]
    with sqlite3.connect(tmp_path / "context.sqlite") as conn:
        row = conn.execute(
            "SELECT status, provider, dimension FROM vector_index_metadata"
        ).fetchone()
    assert row == ("enabled", "not-configured", 0)


def test_build_index_required_sqlite_vec_succeeds_when_dependency_is_installed(
    tmp_path: Path,
) -> None:
    report = build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
        sqlite_vec="required",
    )

    assert report["sqlite_vec"]["mode"] == "required"
    assert report["sqlite_vec"]["status"] == "enabled"


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
