"""Local embedding build and sqlite-vec search helpers."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

DEFAULT_EMBEDDING_PROVIDER = "fastembed"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_EMBEDDING_DIMENSION = 384
DEFAULT_BATCH_SIZE = 64

EmbedTexts = Callable[[list[str]], list[list[float]]]


def build_runtime_embeddings(
    *,
    sqlite_path: Path,
    vector_jsonl_path: Path,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    dimension: int = DEFAULT_EMBEDDING_DIMENSION,
    batch_size: int = DEFAULT_BATCH_SIZE,
    embed_texts: EmbedTexts | None = None,
) -> dict[str, Any]:
    """Embed vector-corpus records into sqlite-vec.

    The generated vector table is a rebuildable runtime artifact. The canonical
    corpus remains ``build/vector-corpus.jsonl``.
    """
    records = _read_vector_records(vector_jsonl_path)
    if provider != DEFAULT_EMBEDDING_PROVIDER and embed_texts is None:
        raise ValueError("only fastembed is implemented unless embed_texts is injected")
    embedder = embed_texts or _fastembed_texts(model_name=model, batch_size=batch_size)
    with sqlite3.connect(sqlite_path) as conn:
        _load_sqlite_vec(conn)
        _reset_vector_tables(conn, dimension=dimension)
        inserted = 0
        for offset in range(0, len(records), batch_size):
            batch = records[offset : offset + batch_size]
            texts = [f"passage: {record['text']}" for record in batch]
            vectors = embedder(texts)
            if len(vectors) != len(batch):
                raise RuntimeError("embedding provider returned a mismatched vector count")
            for record, vector in zip(batch, vectors, strict=True):
                _validate_dimension(vector, dimension)
                rowid = inserted + 1
                metadata = record.get("metadata")
                metadata = metadata if isinstance(metadata, dict) else {}
                canonical_record_id = str(
                    metadata.get("canonical_record_id")
                    or record.get("item_id")
                    or record.get("claim_id")
                    or record["id"]
                )
                conn.execute(
                    """
                    INSERT INTO vector_embedding_records (
                      rowid, id, canonical_record_id, record_type, item_id,
                      claim_id, text, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rowid,
                        str(record["id"]),
                        canonical_record_id,
                        str(metadata.get("record_type") or ""),
                        str(record.get("item_id") or ""),
                        str(record.get("claim_id") or ""),
                        str(record["text"]),
                        json.dumps(metadata, sort_keys=True, ensure_ascii=False),
                    ),
                )
                conn.execute(
                    "INSERT INTO vector_embeddings(rowid, embedding) VALUES (?, ?)",
                    (rowid, json.dumps([float(value) for value in vector])),
                )
                inserted += 1
        _update_vector_metadata(
            conn,
            provider=provider,
            model=model,
            dimension=dimension,
            source=str(vector_jsonl_path),
            vector_records=inserted,
        )
    return {
        "status": "embedded",
        "provider": provider,
        "model": model,
        "dimension": dimension,
        "vector_records": len(records),
        "sqlite": str(sqlite_path),
        "vector_jsonl": str(vector_jsonl_path),
    }


def embed_query(
    query: str,
    *,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[float]:
    if provider != DEFAULT_EMBEDDING_PROVIDER:
        raise ValueError("only fastembed query embedding is implemented")
    embedder = _fastembed_texts(model_name=model, batch_size=1)
    return embedder([f"query: {query}"])[0]


def search_runtime_vectors(
    sqlite_path: Path,
    *,
    query_vector: list[float],
    limit: int = 12,
) -> list[dict[str, Any]]:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        _load_sqlite_vec(conn)
        try:
            rows = conn.execute(
                """
                SELECT
                  vector_embedding_records.id,
                  vector_embedding_records.canonical_record_id,
                  vector_embedding_records.record_type,
                  vector_embedding_records.item_id,
                  vector_embedding_records.claim_id,
                  vector_embedding_records.text,
                  vector_embedding_records.metadata_json,
                  vector_embeddings.distance
                FROM vector_embeddings
                JOIN vector_embedding_records
                  ON vector_embedding_records.rowid = vector_embeddings.rowid
                WHERE vector_embeddings.embedding MATCH ? AND k = ?
                ORDER BY vector_embeddings.distance
                """,
                (json.dumps([float(value) for value in query_vector]), limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [_vector_result(row) for row in rows]


def _read_vector_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"invalid vector record in {path}")
            records.append(record)
    return records


def _fastembed_texts(*, model_name: str, batch_size: int) -> EmbedTexts:
    def embed(texts: list[str]) -> list[list[float]]:
        from fastembed import TextEmbedding

        model = TextEmbedding(model_name=model_name)
        return [list(map(float, vector)) for vector in model.embed(texts, batch_size=batch_size)]

    return embed


def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    import sqlite_vec

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)


def _reset_vector_tables(conn: sqlite3.Connection, *, dimension: int) -> None:
    conn.execute("DROP TABLE IF EXISTS vector_embeddings")
    conn.execute("DROP TABLE IF EXISTS vector_embedding_records")
    conn.execute(
        """
        CREATE TABLE vector_embedding_records (
          rowid INTEGER PRIMARY KEY,
          id TEXT NOT NULL UNIQUE,
          canonical_record_id TEXT NOT NULL,
          record_type TEXT NOT NULL,
          item_id TEXT NOT NULL,
          claim_id TEXT NOT NULL,
          text TEXT NOT NULL,
          metadata_json TEXT NOT NULL
        )
        """
    )
    conn.execute(f"CREATE VIRTUAL TABLE vector_embeddings USING vec0(embedding float[{dimension}])")


def _validate_dimension(vector: list[float], dimension: int) -> None:
    if len(vector) != dimension:
        raise RuntimeError(f"embedding dimension mismatch: expected {dimension}, got {len(vector)}")


def _update_vector_metadata(
    conn: sqlite3.Connection,
    *,
    provider: str,
    model: str,
    dimension: int,
    source: str,
    vector_records: int,
) -> None:
    conn.execute("DELETE FROM vector_index_metadata")
    conn.execute(
        """
        INSERT INTO vector_index_metadata (
          status, provider, model, dimension, source, vector_records,
          content_hash_strategy
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "embedded",
            provider,
            model,
            dimension,
            source,
            vector_records,
            "stable vector record id + text",
        ),
    )


def _vector_result(row: sqlite3.Row) -> dict[str, Any]:
    try:
        metadata = json.loads(str(row["metadata_json"] or "{}"))
    except json.JSONDecodeError:
        metadata = {}
    return {
        "id": str(row["id"]),
        "canonical_record_id": str(row["canonical_record_id"]),
        "record_type": str(row["record_type"]),
        "item_id": str(row["item_id"]),
        "claim_id": str(row["claim_id"]),
        "text": str(row["text"]),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "distance": float(row["distance"]),
    }
