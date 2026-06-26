from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context import index
from sap_agent_context.agent_records import RECORD_FILES


def _write_records_dir(path: Path, *, app_title: str = "Test app") -> None:
    path.mkdir()
    for group, filename in RECORD_FILES.items():
        records = []
        if group == "apps":
            records = [
                {
                    "id": "sap.app.test",
                    "title": app_title,
                    "kind": "sap_app",
                    "status": "active",
                    "access": "public",
                    "requires_login": False,
                    "sap_product": "",
                    "summary": "Test summary",
                    "topics": ["test"],
                    "used_for": ["test"],
                    "retrieval": {"keywords": ["test"], "queries": []},
                    "freshness": {},
                    "source_path": "knowledge/test.yaml",
                }
            ]
        (path / filename).write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )


def test_record_group_loader_reuses_jsonl_until_records_change(tmp_path: Path, monkeypatch) -> None:
    records_dir = tmp_path / "records"
    _write_records_dir(records_dir)
    calls = 0
    original = index._read_jsonl

    def counted_read(path: Path):
        nonlocal calls
        calls += 1
        return original(path)

    monkeypatch.setattr(index, "_read_jsonl", counted_read)
    index._load_record_groups_cached.cache_clear()

    first = index._load_record_groups(records_dir)
    second = index._load_record_groups(records_dir)

    assert first["apps"][0]["title"] == "Test app"
    assert second["apps"][0]["title"] == "Test app"
    assert calls == len(RECORD_FILES)

    (records_dir / RECORD_FILES["apps"]).write_text(
        json.dumps({
            "id": "sap.app.test",
            "title": "Changed app",
            "kind": "sap_app",
            "status": "active",
            "access": "public",
            "requires_login": False,
            "sap_product": "",
            "summary": "Test summary",
            "topics": ["test"],
            "used_for": ["test"],
            "retrieval": {"keywords": ["test"], "queries": []},
            "freshness": {},
            "source_path": "knowledge/test.yaml",
        }) + "\n",
        encoding="utf-8",
    )

    changed = index._load_record_groups(records_dir)
    assert changed["apps"][0]["title"] == "Changed app"
    assert calls == len(RECORD_FILES) * 2
