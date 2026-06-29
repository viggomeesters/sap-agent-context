from __future__ import annotations

import json
from pathlib import Path

import yaml

from sap_agent_context.agent_records import RECORD_FILES

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schema/jsonl-authoring-contract.yaml"
DOC = ROOT / "docs/jsonl-authoring-contract.md"
RECORDS = ROOT / "records"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_jsonl_authoring_contract_declares_canonical_surface_and_legacy_boundary() -> None:
    contract = _contract()

    assert contract["source_of_truth"] == "records/*.jsonl"
    assert contract["legacy_authoring_import"] == "knowledge/**/*.yaml"
    assert contract["compatibility_boundary"]["canonical_agent_surface"] == "records/*.jsonl"
    assert contract["compatibility_boundary"]["current_authoring_format"] == "legacy_yaml_import"
    assert "kind" in contract["common_requirements"]["compatibility_aliases"]


def test_jsonl_authoring_contract_matches_exported_record_files() -> None:
    contract = _contract()
    assert set(contract["required_record_files"]) == set(RECORD_FILES)
    assert "uv run sap-agent-context validate" in contract["verification"]["required_commands"]
    assert set(contract["required_record_files"].values()) == set(RECORD_FILES.values())


def test_exported_jsonl_records_have_contract_provenance_access_and_freshness() -> None:
    contract = _contract()
    item_files = contract["record_types"]["item"]["files"]
    item_required = set(contract["record_types"]["item"]["required_fields"])
    access_allowed = set(contract["common_requirements"]["access_labels"]["allowed"])
    freshness_fields = set(contract["common_requirements"]["freshness"]["fields"])

    for filename in item_files:
        records = _jsonl(RECORDS / filename)
        assert records, filename
        for record in records[:25]:
            assert item_required <= set(record), record["id"]
            assert record["access"] in access_allowed
            assert record["source_ids"], record["id"]
            assert freshness_fields <= set(record["freshness"]), record["id"]
            assert record["kind"], record["id"]


def test_claim_source_relation_records_keep_referential_shape() -> None:
    contract = _contract()
    item_ids = {
        record["id"]
        for filename in contract["record_types"]["item"]["files"]
        for record in _jsonl(RECORDS / filename)
    }

    for record in _jsonl(RECORDS / "claims.jsonl")[:50]:
        assert set(contract["record_types"]["claim"]["required_fields"]) <= set(record)
        assert record["subject_id"] in item_ids
        assert record["evidence_ids"]

    for record in _jsonl(RECORDS / "sources.jsonl")[:50]:
        assert set(contract["record_types"]["source"]["required_fields"]) <= set(record)
        assert record["subject_id"] in item_ids
        assert record["access"] in contract["common_requirements"]["access_labels"]["allowed"]

    for record in _jsonl(RECORDS / "relations.jsonl")[:50]:
        assert set(contract["record_types"]["relation"]["required_fields"]) <= set(record)
        assert record["subject_id"] in item_ids
        assert record["source_ids"]


def test_jsonl_authoring_contract_is_documented_without_yaml_first_language() -> None:
    doc = DOC.read_text(encoding="utf-8")
    assert "records/*.jsonl` is the canonical" in doc
    assert "YAML domain packs are still allowed as legacy authoring/import input" in doc
    assert "Do not mass-rename `kind`" in doc
