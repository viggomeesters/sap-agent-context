from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/fiori-app-tracer-slice-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_fiori_app_tracer_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.fiori-apps-reference-library": "external_reference",
        "sap.app.fiori-app-trace-anchor": "sap_app",
        "sap.object.fiori-app-trace": "sap_object",
        "sap.field-set.fiori-app-trace-core": "sap_field",
        "sap.field-map.fiori-app-traceability": "field_map",
        "sap.role.fiori-business-role-trace": "sap_role",
        "sap.policy.fiori-app-tenant-verification": "access_policy",
        "sap.rule.fiori-app-trace-answer-contract": "decision_rule",
        "sap.test-pattern.fiori-app-trace-answer": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_fiori_app_tracer_separates_source_role_and_tenant_evidence() -> None:
    items = _items_by_id()
    field_map = items["sap.field-map.fiori-app-traceability"]
    rule = items["sap.rule.fiori-app-trace-answer-contract"]
    policy = items["sap.policy.fiori-app-tenant-verification"]

    targets = {step["target"] for step in field_map["mapping_steps"]}
    outcomes = {entry["outcome"] for entry in rule["rules"]}

    assert "Answer.Citation" in targets
    assert "Answer.AuthorizationEvidence" in targets
    assert "Answer.Caveat" in targets
    assert "request app-library/source evidence" in outcomes
    assert "ask for target business role/catalog evidence" in outcomes
    assert "not sufficient evidence for tenant app availability" in policy["claims"][0]["statement"]


def test_fiori_app_tracer_sources_are_link_first_and_fresh() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["review_after"]) == "2026-12-30"
        assert str(item["freshness"]["expires_at"]) == "2027-06-30"
        assert item["release_applicability"]["verification"]
        if item["access"] == "public":
            assert item["source"]["url"].startswith(
                "https://fioriappslibrary.hana.ondemand.com/"
            )
            assert item["source"]["specificity"] == "exact_page"
            assert "do not copy" in item["source"]["license_note"]


def test_fiori_app_tracer_bundle_retrieves_answer_contract() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="agent.answering",
        topic="fiori app trace business catalog role tenant verification source citation",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    selected_ids = {item["id"] for item in bundle["items"]}

    assert bundle["status"] == "ready"
    assert "sap.rule.fiori-app-trace-answer-contract" in selected_ids
    assert "sap.field-map.fiori-app-traceability" in selected_ids
    assert "sap.policy.fiori-app-tenant-verification" in selected_ids
