from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sales-order-output-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_sales_output_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.api-sales-order-process": "external_reference",
        "sap.ref.api-billing-document-process": "external_reference",
        "sap.app.manage-output-items-context": "sap_app",
        "sap.object.sales-order-output": "sap_object",
        "sap.object.billing-document": "sap_object",
        "sap.object.sales-output-item": "sap_object",
        "sap.field-set.sales-order-core": "sap_field",
        "sap.field-set.billing-output-core": "sap_field",
        "sap.field-map.sales-order-output-readiness": "field_map",
        "sap.field-map.billing-output-readiness": "field_map",
        "sap.rule.sales-output-dispatch-readiness": "decision_rule",
        "sap.test-pattern.sales-output-readiness": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_sales_output_separates_order_billing_and_dispatch() -> None:
    items = _items_by_id()
    rule = items["sap.rule.sales-output-dispatch-readiness"]
    sales_map = items["sap.field-map.sales-order-output-readiness"]
    output_map = items["sap.field-map.billing-output-readiness"]

    outcomes = {entry["outcome"] for entry in rule["rules"]}
    sales_targets = {step["target"] for step in sales_map["mapping_steps"]}
    output_targets = {step["target"] for step in output_map["mapping_steps"]}

    assert "billing and output readiness stay held with visible reason" in outcomes
    assert "SalesOrder.BillingHoldReason" in sales_targets
    assert "BillingDocument.AccountingPostingStatus" in output_targets
    assert "OutputItem.Channel" in output_targets
    assert "OutputItem.ProcessingStatus" in output_targets


def test_sales_output_public_items_are_catalog_backed_and_fresh() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["review_after"]) == "2026-12-23"
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"
            assert "copy" in item["source"]["license_note"]


def test_sales_output_bundle_ready_and_not_procurement_or_finance() -> None:
    items = load_items(ROOT)
    sales_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic=(
            "sales order billing output management recipient channel "
            "billing hold dispatch status"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert sales_bundle["status"] == "ready"
    selected_ids = {item["id"] for item in sales_bundle["items"]}
    assert "sap.rule.sales-output-dispatch-readiness" in selected_ids
    assert "sap.field-map.billing-output-readiness" in selected_ids
    assert "sap.field-map.sales-order-output-readiness" in selected_ids
    assert not any(item_id.startswith("sap.rule.ap-") for item_id in selected_ids)
    assert "sap.rule.procurement-workflow-readiness" not in selected_ids
