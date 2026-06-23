from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/finance-ap-supplier-invoice-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_finance_ap_pack_has_invoice_payment_and_rule_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.api-supplier-invoice-process": "external_reference",
        "sap.ref.api-payment-proposal": "external_reference",
        "sap.object.supplier-invoice-ap": "sap_object",
        "sap.object.ap-payment-proposal": "sap_object",
        "sap.field-set.supplier-invoice-ap-core": "sap_field",
        "sap.field-set.ap-payment-proposal-core": "sap_field",
        "sap.field-map.supplier-invoice-ap-core": "field_map",
        "sap.field-map.ap-payment-readiness": "field_map",
        "sap.rule.ap-invoice-payment-separation": "decision_rule",
        "sap.rule.ap-tolerance-and-exception-routing": "decision_rule",
        "sap.test-pattern.ap-invoice-to-payment": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_finance_ap_pack_separates_approval_from_payment() -> None:
    items = _items_by_id()
    rule = items["sap.rule.ap-invoice-payment-separation"]
    payment_map = items["sap.field-map.ap-payment-readiness"]

    outcomes = {entry["outcome"] for entry in rule["rules"]}
    targets = {step["target"] for step in payment_map["mapping_steps"]}

    assert "payment readiness is blocked with reason" in outcomes
    assert "PaymentProposal.PaymentBlock" in targets
    assert "PaymentProposal.ProposalStatus" in targets


def test_finance_ap_public_items_are_catalog_backed() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"
            assert "copy" in item["source"]["license_note"]


def test_finance_ap_bundle_readiness_is_specific_not_generic() -> None:
    items = load_items(ROOT)
    invoice_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.workflow",
        topic="supplier invoice approval payment block payment proposal",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    generic_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.workflow",
        topic="finance unknown invoice analytics kpi",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert invoice_bundle["status"] == "ready"
    assert any(
        item["id"] == "sap.rule.ap-invoice-payment-separation"
        for item in invoice_bundle["items"]
    )
    assert generic_bundle["status"] == "needs_curation"
    assert any("Low topic precision" in gap for gap in generic_bundle["gaps"])
