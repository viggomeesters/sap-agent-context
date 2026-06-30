from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-source-registry-navigation-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_source_registry_pack_has_required_source_families_and_policy_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.source-family-help-portal": "external_reference",
        "sap.ref.source-family-fiori-apps-library": "external_reference",
        "sap.ref.source-family-business-accelerator-hub": "external_reference",
        "sap.ref.source-family-roadmap-explorer": "external_reference",
        "sap.ref.source-family-whats-new-viewer": "external_reference",
        "sap.ref.source-family-sap-learning": "external_reference",
        "sap.ref.source-family-sap-notes-kba": "external_reference",
        "sap.policy.sap-source-registry-access-boundary": "access_policy",
        "sap.rule.sap-source-selection-gate": "decision_rule",
        "sap.fo-pattern.sap-source-registry-answer-proof": "fo_pattern",
        "sap.test-pattern.sap-source-registry-fail-closed": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_source_registry_keeps_public_and_gated_boundaries_explicit() -> None:
    items = _items_by_id()
    help_ref = items["sap.ref.source-family-help-portal"]
    notes_ref = items["sap.ref.source-family-sap-notes-kba"]
    policy = items["sap.policy.sap-source-registry-access-boundary"]

    boundaries = {rule["source_family"]: rule for rule in policy["rules"]}

    assert help_ref["access"] == "public"
    assert help_ref["source"]["kind"] == "public_url"
    assert notes_ref["access"] == "gated"
    assert notes_ref["requires_login"] is True
    assert notes_ref["source"]["kind"] == "gated_url"
    assert (
        boundaries["SAP Notes/KBA"]["forbidden_use"]
        == "copied protected text or unsupported claims"
    )
    assert (
        boundaries["Road Map Explorer"]["proof_boundary"]
        == "delivered-current claim needs product release or tenant proof"
    )


def test_source_selection_gate_maps_claim_types_to_evidence_boundaries() -> None:
    items = _items_by_id()
    gate = items["sap.rule.sap-source-selection-gate"]

    rules = {rule["claim_type"]: rule for rule in gate["rules"]}

    assert (
        rules["concept_explanation"]["preferred_source"]
        == "SAP Help Portal or SAP Learning"
    )
    assert (
        rules["fiori_app_metadata"]["minimum_evidence"]
        == "exact app/source page and product version"
    )
    assert (
        rules["api_or_event_mapping"]["preferred_source"]
        == "SAP Business Accelerator Hub"
    )
    assert (
        rules["planned_future_capability"]["minimum_evidence"]
        == "roadmap pointer plus non-delivered caveat"
    )
    assert rules["support_note_or_kba"]["minimum_evidence"].startswith(
        "authorized human verification"
    )
    assert (
        "source registry pointer is insufficient"
        in rules["tenant_configuration_or_availability"]["minimum_evidence"]
    )


def test_source_registry_answer_proof_slots_and_fail_closed_tests_are_present() -> None:
    items = _items_by_id()
    pattern = items["sap.fo-pattern.sap-source-registry-answer-proof"]
    test_pattern = items["sap.test-pattern.sap-source-registry-fail-closed"]

    slots = {slot["slot"] for slot in pattern["answer_slots"]}
    expected = {scenario["expected"] for scenario in test_pattern["test_scenarios"]}

    assert {
        "source_family",
        "access_boundary",
        "exactness",
        "fail_closed_reason",
        "next_proof",
    } <= slots
    assert "needs_target_tenant_evidence" in expected
    assert "forbidden_gated_content_copy" in expected
    assert "roadmap_is_not_delivery_proof" in expected
    assert "source_labelled_concept_explanation" in expected


def test_source_registry_bundle_retrieves_right_source_for_app_api_and_gated_queries() -> None:
    items = load_items(ROOT)
    fiori_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="agent.answering",
        topic="Fiori app catalog role business catalog tenant availability source evidence",
        sap_product="generic_sap",
        limit=30,
    )
    api_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic="API event integration Business Accelerator Hub exact artifact mapping proof",
        sap_product="generic_sap",
        limit=30,
    )
    gated_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.risk_notes",
        topic="SAP Notes KBA gated S-user copied support text evidence boundary",
        sap_product="generic_sap",
        limit=30,
    )

    fiori_ids = {item["id"] for item in fiori_bundle["items"]}
    api_ids = {item["id"] for item in api_bundle["items"]}
    gated_ids = {item["id"] for item in gated_bundle["items"]}

    assert "sap.ref.source-family-fiori-apps-library" in fiori_ids
    assert "sap.rule.sap-source-selection-gate" in fiori_ids
    assert "sap.ref.source-family-business-accelerator-hub" in api_ids
    assert "sap.ref.source-family-sap-notes-kba" in gated_ids
    assert "sap.policy.sap-source-registry-access-boundary" in gated_ids
