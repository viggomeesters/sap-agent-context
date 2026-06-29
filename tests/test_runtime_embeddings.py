from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from sap_agent_context import cli
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_embeddings import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    build_runtime_embeddings,
    search_runtime_vectors,
)
from sap_agent_context.runtime_search import search_runtime_index

ROOT = Path(__file__).resolve().parents[1]


def _fake_embeddings(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        if "sap.claim.sap-app-eam-pm-ie03" in lowered:
            vectors.append([0.95, 0.05, 0.0])
        elif "sap.app.eam.pm.ie03" in lowered:
            vectors.append([1.0, 0.0, 0.0])
        else:
            vectors.append([0.0, 1.0, 0.0])
    return vectors


@pytest.fixture(scope="module")
def base_index(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    base = tmp_path_factory.mktemp("runtime-embedding-base-index")
    sqlite_path = base / "context.sqlite"
    vector_path = base / "vector-corpus.jsonl"
    build_indexes(
        load_items(ROOT),
        sqlite_path=sqlite_path,
        jsonl_path=base / "items.jsonl",
        vector_jsonl_path=vector_path,
        root=ROOT,
        sqlite_vec="required",
    )
    return sqlite_path, vector_path


def _build_index(tmp_path: Path, base_index: tuple[Path, Path]) -> tuple[Path, Path]:
    sqlite_path = tmp_path / "context.sqlite"
    vector_path = tmp_path / "vector-corpus.jsonl"
    shutil.copy2(base_index[0], sqlite_path)
    shutil.copy2(base_index[1], vector_path)
    return sqlite_path, vector_path


def test_fastembed_defaults_are_clone_first_local_provider() -> None:
    assert DEFAULT_EMBEDDING_PROVIDER == "fastembed"
    assert DEFAULT_EMBEDDING_MODEL == "BAAI/bge-small-en-v1.5"
    assert DEFAULT_EMBEDDING_DIMENSION == 384


def test_build_runtime_embeddings_populates_sqlite_vec_and_metadata(
    tmp_path: Path,
    base_index: tuple[Path, Path],
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)

    report = build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_path,
        provider=DEFAULT_EMBEDDING_PROVIDER,
        model=DEFAULT_EMBEDDING_MODEL,
        dimension=3,
        embed_texts=_fake_embeddings,
    )

    assert report["status"] == "embedded"
    assert report["provider"] == "fastembed"
    assert report["model"] == "BAAI/bge-small-en-v1.5"
    assert report["dimension"] == 3
    assert report["vector_records"] == 1387
    with sqlite3.connect(sqlite_path) as conn:
        metadata = conn.execute(
            """
            SELECT status, provider, model, dimension, vector_records
            FROM vector_index_metadata
            """
        ).fetchone()
        rows = conn.execute("SELECT count(*) FROM vector_embedding_records").fetchone()[0]
    assert metadata == ("embedded", "fastembed", "BAAI/bge-small-en-v1.5", 3, 1387)
    assert rows == 1387


def test_vector_search_returns_nearest_canonical_records(
    tmp_path: Path,
    base_index: tuple[Path, Path],
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)
    build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_path,
        dimension=3,
        embed_texts=_fake_embeddings,
    )

    results = search_runtime_vectors(sqlite_path, query_vector=[1.0, 0.0, 0.0], limit=3)

    assert results[0]["canonical_record_id"] == "sap.app.eam.pm.ie03"
    assert results[0]["record_type"] == "item"
    assert results[0]["distance"] == 0


def test_runtime_search_can_include_vector_results_without_cloud_service(
    tmp_path: Path,
    base_index: tuple[Path, Path],
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)
    build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_path,
        dimension=3,
        embed_texts=_fake_embeddings,
    )

    results = search_runtime_index(
        sqlite_path,
        "semvec-only",
        limit=3,
        query_vector=[1.0, 0.0, 0.0],
    )

    assert results
    assert results[0]["id"] == "sap.app.eam.pm.ie03"
    assert results[0]["source"] == "vector"
    assert results[0]["vector_distance"] == 0


def test_build_embeddings_cli_writes_embedding_metadata(
    tmp_path: Path,
    base_index: tuple[Path, Path],
    monkeypatch,
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)

    def fake_build_runtime_embeddings(**kwargs):
        kwargs["dimension"] = 3
        return build_runtime_embeddings(**kwargs, embed_texts=_fake_embeddings)

    monkeypatch.setattr(cli, "build_runtime_embeddings", fake_build_runtime_embeddings)
    exit_code = cli.main(
        [
            "--root",
            str(ROOT),
            "build-embeddings",
            "--sqlite",
            str(sqlite_path),
            "--vector-jsonl",
            str(vector_path),
        ]
    )

    assert exit_code == 0
    with sqlite3.connect(sqlite_path) as conn:
        row = conn.execute(
            "SELECT status, provider, model, dimension FROM vector_index_metadata"
        ).fetchone()
    assert row == ("embedded", "fastembed", "BAAI/bge-small-en-v1.5", 3)


def test_runtime_search_cli_can_embed_query_when_vector_flag_is_used(
    tmp_path: Path,
    base_index: tuple[Path, Path],
    monkeypatch,
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)
    build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_path,
        dimension=3,
        embed_texts=_fake_embeddings,
    )
    monkeypatch.setattr(cli, "embed_query", lambda *_args, **_kwargs: [1.0, 0.0, 0.0])

    exit_code = cli.main(
        [
            "--root",
            str(ROOT),
            "runtime-search",
            "semvec-only",
            "--sqlite",
            str(sqlite_path),
            "--vector",
            "--limit",
            "1",
        ]
    )

    assert exit_code == 0


def test_vector_merge_does_not_displace_strong_fts_item_result(
    tmp_path: Path,
    base_index: tuple[Path, Path],
) -> None:
    sqlite_path, vector_path = _build_index(tmp_path, base_index)
    build_runtime_embeddings(
        sqlite_path=sqlite_path,
        vector_jsonl_path=vector_path,
        dimension=3,
        embed_texts=_fake_embeddings,
    )

    results = search_runtime_index(
        sqlite_path,
        "IE03 equipment display",
        limit=20,
        query_vector=[1.0, 0.0, 0.0],
        kind="sap_app",
    )

    first_vector_index = next(
        index for index, result in enumerate(results) if result["source"] == "vector"
    )
    assert first_vector_index > 0
    assert all(result["source"] != "vector" for result in results[:first_vector_index])
    assert any(result["exact_token_hits"] > 0 for result in results[:first_vector_index])
