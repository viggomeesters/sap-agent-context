from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/master-data-material-bp.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_master_data_pack_has_required_domain_shapes() -> None:
    items = _items_by_id()

    expected = {
        "sap.ref.api-business-partner": "external_reference",
        "sap.ref.api-product": "external_reference",
        "sap.app.master-data-governance-review": "sap_app",
        "sap.app.product-master-data-review": "sap_app",
        "sap.object.business-partner-core": "sap_object",
        "sap.object.customer-master": "sap_object",
        "sap.object.supplier-master": "sap_object",
        "sap.object.product-master": "sap_object",
        "sap.field-set.business-partner-core": "sap_field",
        "sap.field-set.customer-supplier-role-core": "sap_field",
        "sap.field-set.product-master-core": "sap_field",
        "sap.field-set.company-code-master-data-use": "sap_field",
        "sap.field-map.business-partner-core-identity": "field_map",
        "sap.field-map.bp-role-extension": "field_map",
        "sap.field-map.product-core-identity": "field_map",
        "sap.test-pattern.business-partner-master-data-governance": "test_pattern",
        "sap.test-pattern.product-master-migration-validation": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_master_data_public_items_are_source_backed_and_freshness_labelled() -> None:
    items = _items_by_id()
    for item in items.values():
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith(
                ("https://api.sap.com/", "https://github.com/")
            )
            assert item["source"]["specificity"] in {"catalog_entry", "exact_page"}
            license_note = item["source"]["license_note"]
            assert "copy" in license_note or "MIT" in license_note


def test_master_data_pack_keeps_bp_roles_separate_from_party_identity() -> None:
    items = _items_by_id()
    bp_map = items["sap.field-map.business-partner-core-identity"]
    role_map = items["sap.field-map.bp-role-extension"]

    bp_targets = {step["target"] for step in bp_map["mapping_steps"]}
    role_targets = {step["target"] for step in role_map["mapping_steps"]}

    assert "BusinessPartner.BusinessPartner" in bp_targets
    assert "BusinessPartner.BusinessPartnerCategory" in bp_targets
    assert "Customer.CompanyCode" in role_targets
    assert "Supplier.PurchasingOrganization" in role_targets
    assert "Customer.CompanyCode" not in bp_targets


def test_master_data_bundle_readiness_is_specific_not_broad() -> None:
    items = load_items(ROOT)

    bp_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic="Business partner customer supplier role extension duplicate check",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    product_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="migration.analysis",
        topic="Product material master migration product number base unit product type",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    broad_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic="material master purchasing sales plant",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert bp_bundle["status"] == "ready"
    assert product_bundle["status"] == "ready"
    assert broad_bundle["status"] == "ready"
    assert broad_bundle["gaps"] == []


def test_master_data_pack_defines_negative_test_paths() -> None:
    items = _items_by_id()
    test_items = [item for item in items.values() if item["kind"] == "test_pattern"]

    assert len(test_items) >= 2
    assert all(
        any(case["level"] == "negative" for case in item["test_scenarios"])
        for item in test_items
    )
