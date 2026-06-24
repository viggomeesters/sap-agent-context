from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.agent_records import export_agent_records, validate_agent_records
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_export_agent_records_writes_typed_jsonl_files(tmp_path: Path) -> None:
    report = export_agent_records(load_items(ROOT), tmp_path / "records", root=ROOT)

    assert report["status"] == "exported"
    assert report["source"] == "knowledge/**/*.yaml"
    assert report["canonical_target"] == "records/*.jsonl"
    for name in [
        "apps",
        "tables",
        "fields",
        "workflows",
        "roles",
        "claims",
        "sources",
        "relations",
    ]:
        assert (tmp_path / "records" / f"{name}.jsonl").exists()

    apps = _read_jsonl(tmp_path / "records" / "apps.jsonl")
    assert any(record["id"] == "sap.app.eam.pm.ie03" for record in apps)
    ie03 = next(record for record in apps if record["id"] == "sap.app.eam.pm.ie03")
    assert ie03["kind"] == "sap_app"
    assert ie03["retrieval"]["keywords"]
    assert ie03["freshness"]["review_after"]
    assert ie03["source_ids"]


def test_export_agent_records_splits_claims_sources_and_relations(tmp_path: Path) -> None:
    export_agent_records(load_items(ROOT), tmp_path / "records", root=ROOT)

    claims = _read_jsonl(tmp_path / "records" / "claims.jsonl")
    sources = _read_jsonl(tmp_path / "records" / "sources.jsonl")
    relations = _read_jsonl(tmp_path / "records" / "relations.jsonl")

    assert any(claim["subject_id"] == "sap.app.eam.pm.ie03" for claim in claims)
    claim = next(claim for claim in claims if claim["subject_id"] == "sap.app.eam.pm.ie03")
    assert claim["statement"]
    assert claim["confidence"] in {"low", "medium", "high"}
    assert claim["evidence_ids"]

    assert any(source["subject_id"] == "sap.app.eam.pm.ie03" for source in sources)
    source = next(source for source in sources if source["subject_id"] == "sap.app.eam.pm.ie03")
    assert source["access"] in {"public", "gated", "internal_derived"}
    assert source["license_note"]

    assert all(relation["subject_id"] and relation["target_id"] for relation in relations)
    assert any(relation["type"] == "has_field" for relation in relations)


def test_exported_agent_records_validate_against_json_schema(tmp_path: Path) -> None:
    export_agent_records(load_items(ROOT), tmp_path / "records", root=ROOT)

    report = validate_agent_records(tmp_path / "records", schema_dir=ROOT / "schema")

    assert report["status"] == "passed"
    assert report["files"] == 8
    assert report["records"] > 0
    assert report["issues"] == []
