from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/authorizations-roles-catalogs-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_authorizations_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.s4hana-cloud-iam-overview": "external_reference",
        "sap.app.maintain-business-roles-context": "sap_app",
        "sap.object.business-role-catalog-assignment": "sap_object",
        "sap.role.authorization-administrator": "sap_role",
        "sap.role.display-business-user": "sap_role",
        "sap.policy.authorization-tenant-verification": "access_policy",
        "sap.policy.no-real-user-identities": "access_policy",
        "sap.field-map.authorization-role-catalog-readiness": "field_map",
        "sap.rule.authorization-access-caveat": "decision_rule",
        "sap.test-pattern.authorization-role-catalog-access": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_authorizations_public_items_do_not_cite_internal_derived_evidence() -> None:
    items = _items_by_id()
    internal_ids = {
        item_id for item_id, item in items.items() if item["access"] == "internal_derived"
    }
    for item in items.values():
        if item["access"] != "public":
            continue
        for claim in item.get("claims", []):
            assert not internal_ids.intersection(claim.get("evidence", []))


def test_authorizations_bundle_surfaces_roles_policies_and_caveats() -> None:
    items = load_items(ROOT)
    bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.authorization",
        topic=(
            "authorization business role catalog restriction test user "
            "access caveat"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert bundle["status"] == "ready"
    selected_ids = {item["id"] for item in bundle["items"]}
    selected_kinds = {item["kind"] for item in bundle["items"]}
    assert "sap_role" in selected_kinds
    assert "access_policy" in selected_kinds
    assert "sap.policy.authorization-tenant-verification" in selected_ids
    assert "sap.rule.authorization-access-caveat" in selected_ids
    assert any("tenant verification" in gap.lower() for gap in bundle["gaps"]) is False


def test_authorizations_no_real_user_policy_is_explicit() -> None:
    items = _items_by_id()
    policy = items["sap.policy.no-real-user-identities"]
    test_pattern = items["sap.test-pattern.authorization-role-catalog-access"]

    assert "real user identities" in policy["title"].lower()
    assert any(
        scenario["level"] == "privacy"
        and "synthetic identity" in scenario["expected"]
        for scenario in test_pattern["test_scenarios"]
    )
