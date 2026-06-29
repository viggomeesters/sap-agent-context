from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.agent_records import (
    export_agent_records,
    validate_yaml_jsonl_roundtrip_compatibility,
)
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_yaml_jsonl_roundtrip_preserves_claims_sources_relations_and_workflows(
    tmp_path: Path,
) -> None:
    records_dir = tmp_path / "records"
    items = load_items(ROOT)
    export_agent_records(items, records_dir, root=ROOT)

    report = validate_yaml_jsonl_roundtrip_compatibility(items, records_dir)

    assert report["status"] == "passed"
    assert report["items"] == len(items)
    assert report["records"] > len(items)
    assert "YAML remains legacy import" in report["compatibility_note"]

    workflows = _read_jsonl(records_dir / "workflows.jsonl")
    assert any(record["kind"] == "fo_pattern" for record in workflows)
    assert any(record["kind"] == "decision_rule" for record in workflows)
    assert any(record["kind"] == "test_pattern" for record in workflows)


def test_yaml_jsonl_roundtrip_fails_loudly_when_claims_are_lost(tmp_path: Path) -> None:
    records_dir = tmp_path / "records"
    items = load_items(ROOT)
    export_agent_records(items, records_dir, root=ROOT)
    claims_path = records_dir / "claims.jsonl"
    claims = _read_jsonl(claims_path)
    lost_subject = claims[0]["subject_id"]
    claims_path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in claims[1:]) + "\n",
        encoding="utf-8",
    )

    report = validate_yaml_jsonl_roundtrip_compatibility(items, records_dir)

    assert report["status"] == "failed"
    assert any(
        issue["id"] == lost_subject and "claim count changed" in issue["message"]
        for issue in report["issues"]
    )


def test_yaml_jsonl_roundtrip_fails_loudly_when_item_compat_fields_are_lost(
    tmp_path: Path,
) -> None:
    records_dir = tmp_path / "records"
    items = load_items(ROOT)
    export_agent_records(items, records_dir, root=ROOT)
    apps_path = records_dir / "apps.jsonl"
    apps = _read_jsonl(apps_path)
    apps[0]["topics"] = []
    changed_id = apps[0]["id"]
    apps_path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in apps) + "\n",
        encoding="utf-8",
    )

    report = validate_yaml_jsonl_roundtrip_compatibility(items, records_dir)

    assert report["status"] == "failed"
    assert any(
        issue["id"] == changed_id and "topics changed" in issue["message"]
        for issue in report["issues"]
    )
