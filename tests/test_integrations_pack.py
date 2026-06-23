from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/integrations-api-communication-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_integrations_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.api-billing-document-integration": "external_reference",
        "sap.ref.api-sales-order-integration": "external_reference",
        "sap.app.communication-arrangements-context": "sap_app",
        "sap.object.integration-api-endpoint": "sap_object",
        "sap.object.communication-arrangement-integration": "sap_object",
        "sap.field-set.integration-api-message-core": "sap_field",
        "sap.field-map.integration-api-message-readiness": "field_map",
        "sap.policy.integration-no-secrets": "access_policy",
        "sap.rule.integration-arrangement-readiness": "decision_rule",
        "sap.test-pattern.integration-api-communication": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_integrations_no_secret_boundary_is_explicit() -> None:
    items = _items_by_id()
    policy = items["sap.policy.integration-no-secrets"]
    forbidden_terms = ["credentials", "tenant hostnames", "tokens", "certificates"]

    assert policy["kind"] == "access_policy"
    assert all(term in policy["summary"] for term in forbidden_terms)
    for item in items.values():
        text = yaml.safe_dump(item).lower()
        assert "https://tenant" not in text
        assert "password" not in text
        assert "token_value" not in text


def test_integrations_bundle_has_api_mapping_policy_and_test_pattern() -> None:
    items = load_items(ROOT)
    bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.integration",
        topic=(
            "integration api communication arrangement credentials tenant url "
            "payload business key error handling no secrets"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert bundle["status"] == "ready"
    selected_ids = {item["id"] for item in bundle["items"]}
    selected_kinds = {item["kind"] for item in bundle["items"]}
    assert "sap_app" in selected_kinds
    assert "field_map" in selected_kinds
    assert "test_pattern" in selected_kinds
    assert "sap.policy.integration-no-secrets" in selected_ids
    assert "sap.rule.integration-arrangement-readiness" in selected_ids
    assert "sap.field-map.integration-api-message-readiness" in selected_ids


def test_integrations_public_items_are_catalog_backed() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"
            assert "copy" in item["source"]["license_note"]
