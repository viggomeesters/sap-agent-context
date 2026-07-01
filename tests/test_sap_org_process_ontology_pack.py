from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-org-process-ontology-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_org_process_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.object.sap-org-model-lens": "sap_object",
        "sap.object.sap-org-company-code": "sap_object",
        "sap.object.sap-org-controlling-area": "sap_object",
        "sap.object.sap-org-plant": "sap_object",
        "sap.object.sap-org-storage-location": "sap_object",
        "sap.object.sap-org-sales-organization": "sap_object",
        "sap.object.sap-org-distribution-channel": "sap_object",
        "sap.object.sap-org-purchasing-organization": "sap_object",
        "sap.object.sap-org-business-partner-role": "sap_object",
        "sap.field-set.sap-process-lenses": "sap_field",
        "sap.rule.sap-org-process-evidence-gate": "decision_rule",
        "sap.fo-pattern.sap-org-process-discovery": "fo_pattern",
        "sap.test-pattern.sap-org-process-fail-closed": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_org_objects_distinguish_company_code_plant_and_purchasing_scope() -> None:
    items = _items_by_id()
    org_lens = items["sap.object.sap-org-model-lens"]
    company_code = items["sap.object.sap-org-company-code"]
    plant = items["sap.object.sap-org-plant"]
    purchasing_org = items["sap.object.sap-org-purchasing-organization"]

    org_keys = {unit["key"] for unit in org_lens["org_units"]}

    assert {
        "client_mandant",
        "company_code",
        "controlling_area",
        "plant",
        "storage_location",
        "sales_organization",
        "distribution_channel",
        "purchasing_organization",
        "business_partner_role",
    } <= org_keys
    assert company_code["org_scope"] == "financial_reporting_legal_entity"
    assert plant["org_scope"] == "logistics_valuation_and_operations_node"
    assert purchasing_org["org_scope"] == "procurement_responsibility_and_vendor_negotiation"


def test_process_lenses_route_o2c_p2p_r2r_h2r_and_design_to_operate() -> None:
    items = _items_by_id()
    process_lenses = items["sap.field-set.sap-process-lenses"]
    gate = items["sap.rule.sap-org-process-evidence-gate"]

    process_keys = {process["key"] for process in process_lenses["process_lenses"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}

    assert {"O2C", "P2P", "R2R", "H2R", "D2O"} <= process_keys
    assert "needs_target_org_assignment_evidence" in outcomes
    assert "process_map_is_not_configuration_proof" in outcomes
    assert "public_concept_is_not_implemented_tenant_process" in outcomes


def test_org_process_bundle_handles_company_code_vs_plant_and_purchasing_queries() -> None:
    items = load_items(ROOT)
    org_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="agent.answering",
        topic="company code versus plant controlling area storage location org unit evidence",
        sap_product="generic_sap",
        limit=20,
    )
    purchasing_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.discovery",
        topic=(
            "which org unit owns purchasing P2P purchasing organization "
            "vendor negotiation evidence"
        ),
        sap_product="generic_sap",
        limit=20,
    )

    org_ids = {item["id"] for item in org_bundle["items"]}
    purchasing_ids = {item["id"] for item in purchasing_bundle["items"]}

    assert org_bundle["status"] == "ready"
    assert purchasing_bundle["status"] == "ready"
    assert "sap.object.sap-org-company-code" in org_ids
    assert "sap.object.sap-org-plant" in org_ids
    assert "sap.rule.sap-org-process-evidence-gate" in org_ids
    assert "sap.object.sap-org-purchasing-organization" in purchasing_ids
    assert "sap.field-set.sap-process-lenses" in purchasing_ids


def test_org_process_fail_closed_for_tenant_structure_claims() -> None:
    items = _items_by_id()
    test_pattern = items["sap.test-pattern.sap-org-process-fail-closed"]

    scenarios = {scenario["scenario"]: scenario for scenario in test_pattern["test_scenarios"]}

    assert (
        scenarios["invented target org assignment"]["expected"]
        == "needs_target_org_assignment_evidence"
    )
    assert scenarios["public process map as tenant proof"]["expected"] == "not_configuration_proof"
    assert scenarios["P2P versus O2C classification"]["expected"] == "route_to_process_lens"
