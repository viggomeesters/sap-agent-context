"""Build rebuildable local indexes for SAP Agent Context."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from sap_fo_knowledge_base.model import KnowledgeItem


def build_indexes(
    items: list[KnowledgeItem],
    *,
    sqlite_path: Path,
    jsonl_path: Path,
    vector_jsonl_path: Path,
    root: Path,
) -> dict[str, Any]:
    """Build SQLite, JSONL and vector-ready chunk indexes."""
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    vector_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            CREATE TABLE items (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              kind TEXT NOT NULL,
              status TEXT NOT NULL,
              access TEXT NOT NULL,
              requires_login INTEGER NOT NULL,
              sap_product TEXT NOT NULL,
              review_after TEXT NOT NULL,
              summary TEXT NOT NULL,
              path TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE TABLE item_topics (item_id TEXT NOT NULL, topic TEXT NOT NULL)")
        conn.execute("CREATE TABLE item_used_for (item_id TEXT NOT NULL, used_for TEXT NOT NULL)")
        conn.execute(
            "CREATE VIRTUAL TABLE item_fts USING fts5(id, title, kind, summary, retrieval_text)"
        )
        for item in items:
            rel_path = str(item.path.relative_to(root))
            raw_freshness = item.data.get("freshness")
            freshness: dict[str, Any] = raw_freshness if isinstance(raw_freshness, dict) else {}
            conn.execute(
                """
                INSERT INTO items (
                  id, title, kind, status, access, requires_login, sap_product,
                  review_after, summary, path, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_id,
                    item.title,
                    item.kind,
                    str(item.data.get("status") or ""),
                    item.access,
                    1 if item.data.get("requires_login") else 0,
                    str(item.data.get("sap_product") or ""),
                    str(freshness.get("review_after") or ""),
                    item.summary,
                    rel_path,
                    json.dumps(item.data, sort_keys=True, default=str),
                ),
            )
            conn.execute(
                """
                INSERT INTO item_fts (id, title, kind, summary, retrieval_text)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item.item_id, item.title, item.kind, item.summary, item.text_for_retrieval),
            )
            conn.executemany(
                "INSERT INTO item_topics (item_id, topic) VALUES (?, ?)",
                [(item.item_id, topic) for topic in item.topics],
            )
            conn.executemany(
                "INSERT INTO item_used_for (item_id, used_for) VALUES (?, ?)",
                [(item.item_id, used_for) for used_for in item.used_for],
            )

    _write_jsonl(jsonl_path, (_item_record(item, root) for item in items))
    _write_jsonl(vector_jsonl_path, (_vector_record(item, root) for item in items))
    return {
        "status": "built",
        "items": len(items),
        "sqlite": str(sqlite_path),
        "items_jsonl": str(jsonl_path),
        "vector_jsonl": str(vector_jsonl_path),
    }


def _item_record(item: KnowledgeItem, root: Path) -> dict[str, Any]:
    return {
        "id": item.item_id,
        "title": item.title,
        "kind": item.kind,
        "access": item.access,
        "requires_login": item.data.get("requires_login"),
        "topics": item.topics,
        "used_for": item.used_for,
        "path": str(item.path.relative_to(root)),
        "summary": item.summary,
    }


def _vector_record(item: KnowledgeItem, root: Path) -> dict[str, Any]:
    return {
        "id": f"{item.item_id}#summary",
        "item_id": item.item_id,
        "text": item.text_for_retrieval,
        "metadata": {
            "title": item.title,
            "kind": item.kind,
            "access": item.access,
            "requires_login": item.data.get("requires_login"),
            "topics": item.topics,
            "used_for": item.used_for,
            "path": str(item.path.relative_to(root)),
        },
    }


def _write_jsonl(path: Path, records: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
