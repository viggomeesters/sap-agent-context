from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-foundations-ontology-pack.yaml"
DOC = ROOT / "docs/sap-context-ontology.md"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_sap_foundations_pack_has_required_ontology_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.sap-help-portal-foundation": "external_reference",
        "sap.ref.sap-activate-roadmap-viewer": "external_reference",
        "sap.object.sap-context-foundation": "sap_object",
        "sap.field-set.sap-context-lenses": "sap_field",
        "sap.rule.sap-answer-ontology-gate": "decision_rule",
        "sap.object.sap-landscape-and-lifecycle-context": "sap_object",
        "sap.object.sap-customizing-configuration-context": "sap_object",
        "sap.object.sap-org-process-surface-context": "sap_object",
        "sap.fo-pattern.sap-from-zero-answer": "fo_pattern",
        "sap.test-pattern.sap-foundation-fail-closed": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_sap_foundation_gate_requires_lenses_and_fail_closed_stance() -> None:
    items = _items_by_id()
    field_set = items["sap.field-set.sap-context-lenses"]
    gate = items["sap.rule.sap-answer-ontology-gate"]
    test_pattern = items["sap.test-pattern.sap-foundation-fail-closed"]

    field_keys = {field["key"] for field in field_set["field_definitions"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}
    expected_cases = {scenario["expected"] for scenario in test_pattern["test_scenarios"]}

    assert {
        "SapContext.Surface",
        "SapContext.Applicability",
        "SapContext.TenantDependency",
        "SapContext.Evidence",
        "SapContext.OutputStance",
    } <= field_keys
    assert "needs_tenant_evidence" in outcomes
    assert "caveated answer; no tenant availability claim." in expected_cases


def test_sap_context_ontology_doc_names_core_lenses_and_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in [
        "Foundation",
        "Lifecycle",
        "Landscape",
        "Edition/release",
        "Configuration",
        "Organization",
        "Process/capability",
        "Surface",
        "Source/evidence",
        "No copied SAP Help",
        "No tenant-specific customizing values",
    ]:
        assert phrase in text


def test_sap_foundation_bundle_retrieves_from_zero_and_customizing_context() -> None:
    items = load_items(ROOT)
    foundation_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="agent.context",
        topic="SAP foundation lifecycle landscape customizing evidence",
        sap_product="generic_sap",
        limit=20,
    )
    customizing_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.business_rules",
        topic="SPRO IMG customizing tenant evidence company code configuration",
        sap_product="generic_sap",
        limit=12,
    )

    foundation_ids = {item["id"] for item in foundation_bundle["items"]}
    customizing_ids = {item["id"] for item in customizing_bundle["items"]}

    assert foundation_bundle["status"] == "ready"
    assert customizing_bundle["status"] == "ready"
    assert "sap.object.sap-context-foundation" in foundation_ids
    assert "sap.rule.sap-answer-ontology-gate" in foundation_ids
    assert "sap.object.sap-customizing-configuration-context" in customizing_ids
