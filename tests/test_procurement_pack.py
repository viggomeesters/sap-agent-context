from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/procurement-pr-po-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_procurement_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.api-purchase-requisition-process": "external_reference",
        "sap.ref.api-purchase-order-process": "external_reference",
        "sap.app.manage-purchase-requisitions-context": "sap_app",
        "sap.object.purchase-requisition-pr-po": "sap_object",
        "sap.object.purchase-order": "sap_object",
        "sap.field-set.purchase-requisition-core": "sap_field",
        "sap.field-set.purchase-order-core": "sap_field",
        "sap.field-map.pr-to-po-readiness": "field_map",
        "sap.field-map.po-fulfillment-readiness": "field_map",
        "sap.rule.procurement-workflow-readiness": "decision_rule",
        "sap.test-pattern.procurement-pr-po-readiness": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_procurement_pack_separates_pr_approval_po_and_receipt() -> None:
    items = _items_by_id()
    rule = items["sap.rule.procurement-workflow-readiness"]
    pr_map = items["sap.field-map.pr-to-po-readiness"]
    po_map = items["sap.field-map.po-fulfillment-readiness"]

    outcomes = {entry["outcome"] for entry in rule["rules"]}
    pr_targets = {step["target"] for step in pr_map["mapping_steps"]}
    po_targets = {step["target"] for step in po_map["mapping_steps"]}

    assert "block PO conversion and assign sourcing owner" in outcomes
    assert "PurchaseRequisition.WorkflowStatus" in pr_targets
    assert "PurchaseRequisition.FixedSupplier" in pr_targets
    assert "PurchaseOrder.GoodsReceiptIsExpected" in po_targets
    assert "PurchaseOrder.InvoiceIsExpected" in po_targets


def test_procurement_public_items_are_catalog_backed_and_fresh() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["review_after"]) == "2026-12-23"
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"
            assert "copy" in item["source"]["license_note"]


def test_procurement_bundle_readiness_is_specific_not_generic() -> None:
    items = load_items(ROOT)
    procurement_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic=(
            "purchase requisition workflow source of supply account assignment "
            "purchase order goods receipt"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    generic_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic="procurement unknown dashboard analytics kpi",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert procurement_bundle["status"] == "ready"
    assert any(
        item["id"] == "sap.rule.procurement-workflow-readiness"
        for item in procurement_bundle["items"]
    )
    assert any(
        item["id"] == "sap.field-map.po-fulfillment-readiness"
        for item in procurement_bundle["items"]
    )
    assert generic_bundle["status"] == "needs_curation"
    assert any("Low topic precision" in gap for gap in generic_bundle["gaps"])
