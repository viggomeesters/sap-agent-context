from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-landscape-activate-customizing-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_landscape_activate_customizing_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.object.sap-activate-lifecycle": "sap_object",
        "sap.object.sap-system-landscape": "sap_object",
        "sap.object.sap-configuration-surface": "sap_object",
        "sap.object.sap-org-structure-scope": "sap_object",
        "sap.rule.sap-landscape-evidence-gate": "decision_rule",
        "sap.rule.sap-customizing-proof-gate": "decision_rule",
        "sap.fo-pattern.sap-phase-landscape-customizing-discovery": "fo_pattern",
        "sap.test-pattern.sap-landscape-customizing-fail-closed": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_activate_lifecycle_and_landscape_keep_phase_and_system_evidence_separate() -> None:
    items = _items_by_id()
    lifecycle = items["sap.object.sap-activate-lifecycle"]
    landscape = items["sap.object.sap-system-landscape"]
    gate = items["sap.rule.sap-landscape-evidence-gate"]

    phases = {phase["phase"] for phase in lifecycle["lifecycle_phases"]}
    layers = {layer["layer"] for layer in landscape["landscape_layers"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}

    assert {"Discover", "Prepare", "Explore", "Realize", "Deploy", "Run"} <= phases
    assert {"DEV", "QAS", "PRD"} <= layers
    assert "ask for fit-to-standard, gap and design evidence" in outcomes
    assert "test/acceptance evidence, not production operations truth" in outcomes


def test_customizing_gate_distinguishes_configuration_surface_and_org_scope() -> None:
    items = _items_by_id()
    configuration = items["sap.object.sap-configuration-surface"]
    org_scope = items["sap.object.sap-org-structure-scope"]
    gate = items["sap.rule.sap-customizing-proof-gate"]

    surfaces = {surface["surface"] for surface in configuration["configuration_surfaces"]}
    org_units = {unit["key"] for unit in org_scope["org_units"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}

    assert {"SPRO/IMG", "CBC", "SSCUI", "Master data", "Extension/code"} <= surfaces
    assert {"company_code", "plant", "sales_organization", "purchasing_organization"} <= org_units
    assert "needs_product_edition_release" in outcomes
    assert "needs_tenant_evidence" in outcomes
    assert "needs_target_customizing_evidence" in outcomes


def test_landscape_customizing_bundle_retrieves_phase_and_configuration_gates() -> None:
    items = load_items(ROOT)
    phase_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="implementation.lifecycle",
        topic="SAP Activate Explore Realize DEV QAS PRD landscape evidence",
        sap_product="generic_sap",
        limit=12,
    )
    customizing_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.business_rules",
        topic="SPRO IMG CBC SSCUI customizing company code tenant evidence",
        sap_product="generic_sap",
        limit=12,
    )

    phase_ids = {item["id"] for item in phase_bundle["items"]}
    customizing_ids = {item["id"] for item in customizing_bundle["items"]}

    assert phase_bundle["status"] == "ready"
    assert customizing_bundle["status"] == "ready"
    assert "sap.rule.sap-landscape-evidence-gate" in phase_ids
    assert "sap.object.sap-activate-lifecycle" in phase_ids
    assert "sap.rule.sap-customizing-proof-gate" in customizing_ids
    assert "sap.object.sap-configuration-surface" in customizing_ids
