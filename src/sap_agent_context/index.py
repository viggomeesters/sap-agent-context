"""Build rebuildable local indexes for SAP Agent Context."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from sap_agent_context.agent_records import RECORD_FILES, export_agent_records
from sap_agent_context.model import KnowledgeItem

ITEM_RECORD_GROUPS = ["apps", "tables", "fields", "workflows", "roles"]


def build_indexes(
    items: list[KnowledgeItem],
    *,
    sqlite_path: Path,
    jsonl_path: Path,
    vector_jsonl_path: Path,
    root: Path,
) -> dict[str, Any]:
    """Build SQLite, JSONL and vector-ready chunk indexes.

    Runtime SQLite is derived from canonical agent-first records/*.jsonl when
    available. When records are absent, the current YAML items are exported to a
    temporary records directory first so the build remains backward compatible.
    """
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    vector_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    records_dir, temp_dir = _records_dir_or_temp(items, root)
    try:
        records = _load_record_groups(records_dir)
        item_records = _item_records(records)
        _build_sqlite(sqlite_path, item_records=item_records, records=records)
        _write_jsonl(jsonl_path, item_records)
        vector_records = [
            *(_vector_record(record) for record in item_records),
            *(_claim_vector_record(record) for record in records["claims"]),
        ]
        _write_jsonl(vector_jsonl_path, vector_records)
        return {
            "status": "built",
            "items": len(item_records),
            "claims": len(records["claims"]),
            "sources": len(records["sources"]),
            "relations": len(records["relations"]),
            "vector_records": len(vector_records),
            "sqlite": str(sqlite_path),
            "items_jsonl": str(jsonl_path),
            "vector_jsonl": str(vector_jsonl_path),
            "records_source": str(records_dir),
        }
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def _records_dir_or_temp(
    items: list[KnowledgeItem],
    root: Path,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    records_dir = root / "records"
    if all((records_dir / filename).exists() for filename in RECORD_FILES.values()):
        return records_dir, None
    temp_dir = tempfile.TemporaryDirectory(prefix="sap-agent-context-records-")
    output_dir = Path(temp_dir.name)
    export_agent_records(items, output_dir, root=root)
    return output_dir, temp_dir


def _load_record_groups(records_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        group: _read_jsonl(records_dir / filename)
        for group, filename in RECORD_FILES.items()
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _item_records(records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for group in ITEM_RECORD_GROUPS:
        merged.extend(records[group])
    return sorted(merged, key=lambda record: str(record["id"]))


def _build_sqlite(
    sqlite_path: Path,
    *,
    item_records: list[dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
) -> None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
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
              expires_at TEXT NOT NULL,
              summary TEXT NOT NULL,
              path TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE claims (
              id TEXT PRIMARY KEY,
              subject_id TEXT NOT NULL,
              statement TEXT NOT NULL,
              confidence TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE sources (
              id TEXT PRIMARY KEY,
              subject_id TEXT NOT NULL,
              kind TEXT NOT NULL,
              access TEXT NOT NULL,
              url TEXT NOT NULL,
              license_note TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE relations (
              id TEXT PRIMARY KEY,
              subject_id TEXT NOT NULL,
              type TEXT NOT NULL,
              target_id TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE TABLE item_topics (item_id TEXT NOT NULL, topic TEXT NOT NULL)")
        conn.execute("CREATE TABLE item_used_for (item_id TEXT NOT NULL, used_for TEXT NOT NULL)")
        conn.execute(
            "CREATE VIRTUAL TABLE item_fts USING fts5(id, title, kind, summary, retrieval_text)"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE claim_fts USING fts5(id, subject_id, statement, evidence_text)"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE source_fts USING fts5(id, subject_id, title, license_note, url)"
        )
        _insert_items(conn, item_records)
        _insert_claims(conn, records["claims"])
        _insert_sources(conn, records["sources"])
        _insert_relations(conn, records["relations"])
        conn.execute("CREATE INDEX idx_items_kind ON items(kind)")
        conn.execute("CREATE INDEX idx_items_access ON items(access)")
        conn.execute("CREATE INDEX idx_claims_subject ON claims(subject_id)")
        conn.execute("CREATE INDEX idx_sources_subject ON sources(subject_id)")
        conn.execute("CREATE INDEX idx_relations_subject_type ON relations(subject_id, type)")
        conn.execute("CREATE INDEX idx_relations_target ON relations(target_id)")


def _insert_items(conn: sqlite3.Connection, item_records: list[dict[str, Any]]) -> None:
    for record in item_records:
        freshness = record.get("freshness") if isinstance(record.get("freshness"), dict) else {}
        retrieval = record.get("retrieval") if isinstance(record.get("retrieval"), dict) else {}
        topics = _strings(record.get("topics"))
        used_for = _strings(record.get("used_for"))
        conn.execute(
            """
            INSERT INTO items (
              id, title, kind, status, access, requires_login, sap_product,
              review_after, expires_at, summary, path, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["title"],
                record["kind"],
                str(record.get("status") or ""),
                record["access"],
                1 if record.get("requires_login") else 0,
                str(record.get("sap_product") or ""),
                str(freshness.get("review_after") or ""),
                str(freshness.get("expires_at") or ""),
                record["summary"],
                str(record.get("source_path") or ""),
                json.dumps(record, sort_keys=True, default=str, ensure_ascii=False),
            ),
        )
        retrieval_text = " ".join(
            [
                record["id"],
                record["title"],
                record["kind"],
                record["summary"],
                " ".join(topics),
                " ".join(used_for),
                " ".join(_strings(retrieval.get("keywords"))),
                " ".join(_strings(retrieval.get("queries"))),
            ]
        )
        conn.execute(
            """
            INSERT INTO item_fts (id, title, kind, summary, retrieval_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (record["id"], record["title"], record["kind"], record["summary"], retrieval_text),
        )
        conn.executemany(
            "INSERT INTO item_topics (item_id, topic) VALUES (?, ?)",
            [(record["id"], topic) for topic in topics],
        )
        conn.executemany(
            "INSERT INTO item_used_for (item_id, used_for) VALUES (?, ?)",
            [(record["id"], value) for value in used_for],
        )


def _insert_claims(conn: sqlite3.Connection, claims: list[dict[str, Any]]) -> None:
    for record in claims:
        evidence_text = " ".join(_strings(record.get("evidence_ids")))
        conn.execute(
            """
            INSERT INTO claims (id, subject_id, statement, confidence, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["subject_id"],
                record["statement"],
                record["confidence"],
                json.dumps(record, sort_keys=True, default=str, ensure_ascii=False),
            ),
        )
        conn.execute(
            """
            INSERT INTO claim_fts (id, subject_id, statement, evidence_text)
            VALUES (?, ?, ?, ?)
            """,
            (record["id"], record["subject_id"], record["statement"], evidence_text),
        )


def _insert_sources(conn: sqlite3.Connection, sources: list[dict[str, Any]]) -> None:
    for record in sources:
        conn.execute(
            """
            INSERT INTO sources (id, subject_id, kind, access, url, license_note, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["subject_id"],
                record["kind"],
                record["access"],
                str(record.get("url") or ""),
                record["license_note"],
                json.dumps(record, sort_keys=True, default=str, ensure_ascii=False),
            ),
        )
        conn.execute(
            """
            INSERT INTO source_fts (id, subject_id, title, license_note, url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["subject_id"],
                record["title"],
                record["license_note"],
                str(record.get("url") or ""),
            ),
        )


def _insert_relations(conn: sqlite3.Connection, relations: list[dict[str, Any]]) -> None:
    for record in relations:
        conn.execute(
            """
            INSERT INTO relations (id, subject_id, type, target_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["subject_id"],
                record["type"],
                record["target_id"],
                json.dumps(record, sort_keys=True, default=str, ensure_ascii=False),
            ),
        )


def _vector_record(record: dict[str, Any]) -> dict[str, Any]:
    retrieval = record.get("retrieval") if isinstance(record.get("retrieval"), dict) else {}
    text = " ".join(
        [
            str(record["id"]),
            str(record["title"]),
            str(record["summary"]),
            " ".join(_strings(record.get("topics"))),
            " ".join(_strings(record.get("used_for"))),
            " ".join(_strings(retrieval.get("keywords"))),
            " ".join(_strings(retrieval.get("queries"))),
        ]
    )
    return {
        "id": f"{record['id']}#summary",
        "item_id": record["id"],
        "text": text,
        "metadata": {
            "record_type": "item",
            "canonical_record_id": record["id"],
            "title": record["title"],
            "kind": record["kind"],
            "access": record["access"],
            "requires_login": record.get("requires_login"),
            "sap_product": str(record.get("sap_product") or ""),
            "topics": _strings(record.get("topics")),
            "used_for": _strings(record.get("used_for")),
            "source_path": str(record.get("source_path") or ""),
        },
    }


def _claim_vector_record(record: dict[str, Any]) -> dict[str, Any]:
    evidence_ids = _strings(record.get("evidence_ids"))
    constraints = _strings(record.get("usage_constraints"))
    text = " ".join(
        [
            str(record["id"]),
            str(record["subject_id"]),
            str(record["statement"]),
            f"confidence {record['confidence']}",
            "evidence " + " ".join(evidence_ids),
            " ".join(constraints),
        ]
    )
    return {
        "id": f"{record['id']}#statement",
        "claim_id": record["id"],
        "text": text,
        "metadata": {
            "record_type": "claim",
            "canonical_record_id": record["id"],
            "subject_id": record["subject_id"],
            "kind": "claim",
            "confidence": record["confidence"],
            "evidence_ids": evidence_ids,
        },
    }


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _write_jsonl(path: Path, records: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, default=str, ensure_ascii=False) + "\n")
