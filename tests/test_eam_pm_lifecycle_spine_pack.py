from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.domain_density import build_domain_density_heatmap
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/eam-pm-lifecycle-spine-pack.yaml"


def _items() -> list[dict]:
    payload = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return payload["items"]


def test_eam_pm_lifecycle_spine_pack_has_public_safe_source_labels() -> None:
    items = _items()
    assert len(items) >= 15
    assert any(item["id"] == "sap.ref.eam.pm.sap-help-task-list-display" for item in items)
    assert any(item["access"] == "public" for item in items)
    assert any(item["access"] == "internal_derived" for item in items)

    text = PACK.read_text(encoding="utf-8").lower()
    forbidden = ["customer", "client tenant url", ".env", "password", "secret_key"]
    assert not any(term in text for term in forbidden)
    for item in items:
        assert item["freshness"]["review_after"]
        assert item["source"]["license_note"]


def test_eam_pm_lifecycle_spine_covers_missing_lifecycle_slices() -> None:
    report = build_domain_density_heatmap(load_items(ROOT))
    slices = report["eam_pm_lifecycle"]

    for name in [
        "maintenance-plan",
        "task-list",
        "measuring-point-counter",
        "work-center",
        "settlement",
        "permits-safety",
    ]:
        assert slices[name]["items"] >= 1, name
        assert slices[name]["status"] != "missing", name

    assert slices["maintenance-plan"]["kind_counts"]["sap_object"] >= 1
    assert slices["task-list"]["kind_counts"]["sap_object"] >= 1
    assert slices["measuring-point-counter"]["kind_counts"]["sap_object"] >= 1
    assert slices["work-center"]["kind_counts"]["sap_object"] >= 1


def test_eam_pm_lifecycle_spine_relates_objects_rules_and_tests() -> None:
    by_id = {item["id"]: item for item in _items()}

    field_set = by_id["sap.field-set.eam-pm-lifecycle-planning"]
    assert {
        "sap.object.eam-maintenance-plan",
        "sap.object.eam-task-list",
        "sap.object.eam-measuring-point-counter",
        "sap.object.eam-work-center",
        "sap.object.eam-settlement-caveat",
    } <= set(field_set["relations"]["objects"])

    rule = by_id["sap.rule.eam.pm-lifecycle-fail-closed"]
    assert "settlement" in rule["topics"]
    assert "permit" in rule["topics"]
    assert any("tenant" in str(step["then"]).lower() for step in rule["rules"])

    test_pattern = by_id["sap.test-pattern.eam-pm-lifecycle-spine-coverage"]
    assert "sap.rule.eam.pm-lifecycle-fail-closed" in test_pattern["claims"][0]["evidence"]
