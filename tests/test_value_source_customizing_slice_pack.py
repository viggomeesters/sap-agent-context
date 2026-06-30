from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/value-source-customizing-slice-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_value_source_customizing_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.object.value-source-classification": "sap_object",
        "sap.field-set.value-source-classification-core": "sap_field",
        "sap.field-map.value-source-customizing-evidence": "field_map",
        "sap.rule.value-source-customizing-ready-gate": "decision_rule",
        "sap.test-pattern.value-source-customizing-gate": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_value_source_customizing_gate_separates_kinds_lookup_and_fallback() -> None:
    items = _items_by_id()
    field_set = items["sap.field-set.value-source-classification-core"]
    field_map = items["sap.field-map.value-source-customizing-evidence"]
    rule = items["sap.rule.value-source-customizing-ready-gate"]

    field_keys = {field["key"] for field in field_set["field_definitions"]}
    targets = {step["target"] for step in field_map["mapping_steps"]}
    outcomes = {entry["outcome"] for entry in rule["rules"]}

    assert "ValueSource.Kind" in field_keys
    assert "ValueSource.LookupAnchor" in field_keys
    assert "ValueSource.FallbackBehavior" in field_keys
    assert "ValueSource.ValueEvidence" in targets
    assert "needs_value_evidence" in outcomes
    assert "needs_derivation_rule" in outcomes
    assert "needs_curation_fallback" in outcomes


def test_value_source_customizing_pack_is_source_backed_and_fresh() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["review_after"]) == "2026-12-30"
        assert str(item["freshness"]["expires_at"]) == "2027-06-30"
        assert item["release_applicability"]["verification"]
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://github.com/")
            assert item["source"]["specificity"] == "exact_page"
            assert "MIT" in item["source"]["license_note"]


def test_value_source_customizing_bundle_retrieves_gate_for_company_code() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="migration.analysis",
        topic="company code value source customizing lookup fallback tenant evidence",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    selected_ids = {item["id"] for item in bundle["items"]}

    assert bundle["status"] == "ready"
    assert "sap.rule.value-source-customizing-ready-gate" in selected_ids
    assert "sap.field-map.value-source-customizing-evidence" in selected_ids
