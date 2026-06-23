from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/material-master-object-anchors-pack.yaml"


def test_material_master_object_anchor_pack_has_required_shapes() -> None:
    items = {item["id"]: item for item in yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]}
    required = {
        "sap.ref.material-product-master-learning": "external_reference",
        "sap.ref.api-product-material": "external_reference",
        "sap.object.material-product-master-anchor": "sap_object",
        "sap.object.material-plant-data": "sap_object",
        "sap.object.material-storage-location": "sap_object",
        "sap.object.material-valuation-accounting": "sap_object",
        "sap.object.material-purchasing-view": "sap_object",
        "sap.object.material-sales-view": "sap_object",
        "sap.object.material-mrp-view": "sap_object",
        "sap.rule.material-master-tenant-view-caveat": "decision_rule",
    }
    for item_id, kind in required.items():
        assert items[item_id]["kind"] == kind


def test_material_master_anchor_pack_is_source_labelled_and_caveated() -> None:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    for item in data["items"]:
        assert item["access"] in {"public", "internal_derived"}
        assert item["freshness"]["review_after"]
        assert item["freshness"]["expires_at"]
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://")
        else:
            assert item["source"]["kind"] == "internal_pattern"
    text = PACK.read_text(encoding="utf-8").lower()
    assert "do not invent tenant-specific" in text
    assert "tenant verification" in text or "tenant-specific" in text


def test_specific_material_master_views_probe_selects_new_anchors() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.business_rules",
        topic="material master views plant storage valuation MRP purchasing sales tenant caveat",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    selected = {item["id"] for item in bundle["items"]}
    assert bundle["status"] == "ready"
    assert "sap.object.material-product-master-anchor" in selected
    assert "sap.rule.material-master-tenant-view-caveat" in selected


def test_broad_material_master_query_is_ready_after_material_anchor_child() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.field_mapping",
        topic="material master purchasing sales plant",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["status"] == "ready"
    assert bundle["gaps"] == []
