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
        "sap.pattern.integration.communication-arrangement-fo": "fo_pattern",
        "sap.pattern.integration-error-retry-fo": "fo_pattern",
        "sap.rule.integration-secret-redaction-fail-closed": "decision_rule",
        "sap.rule.integration-error-retry-fail-closed": "decision_rule",
        "sap.test-pattern.integration-error-retry-redaction": "test_pattern",
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


def test_integrations_deep_slice_has_fail_closed_fo_patterns() -> None:
    items = _items_by_id()
    arrangement = items["sap.pattern.integration.communication-arrangement-fo"]
    retry = items["sap.pattern.integration-error-retry-fo"]
    redaction = items["sap.rule.integration-secret-redaction-fail-closed"]
    retry_rule = items["sap.rule.integration-error-retry-fail-closed"]
    test_pattern = items["sap.test-pattern.integration-error-retry-redaction"]

    assert arrangement["kind"] == "fo_pattern"
    assert "sap.policy.integration-no-secrets" in arrangement["relations"]["access_policies"]
    assert "sap.rule.integration-secret-redaction-fail-closed" in arrangement["relations"]["rules"]

    assert retry["kind"] == "fo_pattern"
    assert "sap.rule.integration-error-retry-fail-closed" in retry["relations"]["rules"]
    assert (
        "sap.test-pattern.integration-error-retry-redaction"
        in retry["relations"]["test_patterns"]
    )

    redaction_outcomes = "\n".join(rule["outcome"] for rule in redaction["rules"])
    assert "reject/redact" in redaction_outcomes
    assert "open verification" in redaction_outcomes

    retry_outcomes = "\n".join(rule["outcome"] for rule in retry_rule["rules"])
    assert "block implementation-ready" in retry_outcomes
    assert "negative test scenarios" in retry_outcomes

    levels = {case["level"] for case in test_pattern["test_scenarios"]}
    assert {"acceptance", "negative", "security"}.issubset(levels)


def test_integrations_bundle_surfaces_deep_security_boundary() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.integration",
        topic=(
            "communication arrangement auth method no secrets redaction tenant verification "
            "retry idempotency business key duplicate error handling"
        ),
        sap_product="s4hana_cloud_public",
        limit=40,
    )

    selected_ids = {item["id"] for item in bundle["items"]}
    assert bundle["status"] == "ready"
    assert "sap.pattern.integration.communication-arrangement-fo" in selected_ids
    assert "sap.pattern.integration-error-retry-fo" in selected_ids
    assert "sap.rule.integration-error-retry-fail-closed" in selected_ids
    assert "sap.test-pattern.integration-error-retry-redaction" in selected_ids


def test_integrations_public_items_are_catalog_backed() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"
            assert "copy" in item["source"]["license_note"]
