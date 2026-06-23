from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/material-eam-spares-bom-links-pack.yaml"


def test_eam_spares_bom_pack_has_required_shapes() -> None:
    items = {item["id"]: item for item in yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]}
    required = {
        "sap.object.eam-spare-part-material": "sap_object",
        "sap.object.eam-equipment-bom": "sap_object",
        "sap.object.eam-functional-location-bom": "sap_object",
        "sap.object.eam-maintenance-order-component": "sap_object",
        "sap.rule.eam-spares-stock-availability-caveat": "decision_rule",
        "sap.field-map.eam-spares-bom-material-link": "field_map",
        "sap.test-pattern.eam-spares-bom-links": "test_pattern",
    }
    for item_id, kind in required.items():
        assert items[item_id]["kind"] == kind


def test_eam_spares_bom_pack_is_public_safe_and_caveated() -> None:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    for item in data["items"]:
        assert item["access"] == "internal_derived"
        assert item["source"]["kind"] == "internal_pattern"
        assert item["freshness"]["review_after"]
        assert item["freshness"]["expires_at"]
    text = PACK.read_text(encoding="utf-8").lower()
    assert "no customer data" in text
    assert "verify" in text
    assert "do not invent" in text


def test_equipment_bom_spares_query_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.field_mapping",
        topic="equipment BOM spare parts material master component maintenance order",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    selected = {item["id"] for item in bundle["items"]}
    assert bundle["status"] == "ready"
    assert "sap.object.eam-equipment-bom" in selected
    assert "sap.object.eam-spare-part-material" in selected
    assert "sap.field-map.eam-spares-bom-material-link" in selected


def test_spare_stock_availability_query_has_caveat() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.business_rules",
        topic="spare part stock availability material MMBE reservation maintenance order component",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    selected = {item["id"] for item in bundle["items"]}
    text = "\n".join(item["summary"] for item in bundle["items"]).lower()
    assert bundle["status"] == "ready"
    assert "sap.rule.eam-spares-stock-availability-caveat" in selected
    assert "do not promise stock exists" in text or "live stock" in text
