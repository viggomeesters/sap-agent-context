from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-alias-evolution-map-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_alias_evolution_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.object.sap-term-alias-evolution": "sap_object",
        "sap.object.sap-migration-term-evolution": "sap_object",
        "sap.object.sap-workflow-term-evolution": "sap_object",
        "sap.rule.sap-alias-evolution-gate": "decision_rule",
        "sap.fo-pattern.sap-alias-evolution-discovery": "fo_pattern",
        "sap.test-pattern.sap-alias-evolution-fail-closed": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_migration_aliases_require_release_and_app_source_evidence() -> None:
    items = _items_by_id()
    migration = items["sap.object.sap-migration-term-evolution"]
    gate = items["sap.rule.sap-alias-evolution-gate"]

    aliases = {alias["term"]: alias for alias in migration["aliases"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}

    assert {"LTMC", "Migration Cockpit", "Migrate Your Data"} <= set(aliases)
    assert aliases["LTMC"]["stance"] == "legacy_or_context_specific_term"
    assert "needs_release_edition_disambiguation" in outcomes
    assert "needs_app_source_evidence" in outcomes
    assert "caveat_alias_evolution_not_one_to_one" in outcomes


def test_workflow_aliases_require_generation_context() -> None:
    items = _items_by_id()
    workflow = items["sap.object.sap-workflow-term-evolution"]
    gate = items["sap.rule.sap-alias-evolution-gate"]

    aliases = {alias["term"] for alias in workflow["aliases"]}
    outcomes = {rule["outcome"] for rule in gate["rules"]}

    assert {
        "SAP Business Workflow",
        "Flexible Workflow",
        "Workflow Management",
        "Build Process Automation",
    } <= aliases
    assert "needs_workflow_generation_context" in outcomes


def test_alias_evolution_bundle_retrieves_ltmc_and_workflow_disambiguation() -> None:
    items = load_items(ROOT)
    migration_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="migration.analysis",
        topic="LTMC Migration Cockpit Migrate Your Data release edition alias",
        sap_product="generic_sap",
        limit=12,
    )
    workflow_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.workflow",
        topic="SAP Business Workflow Flexible Workflow Build Process Automation generation",
        sap_product="generic_sap",
        limit=12,
    )

    migration_ids = {item["id"] for item in migration_bundle["items"]}
    workflow_ids = {item["id"] for item in workflow_bundle["items"]}

    assert migration_bundle["status"] == "ready"
    assert workflow_bundle["status"] == "ready"
    assert "sap.object.sap-migration-term-evolution" in migration_ids
    assert "sap.rule.sap-alias-evolution-gate" in migration_ids
    assert "sap.object.sap-workflow-term-evolution" in workflow_ids
    assert "sap.rule.sap-alias-evolution-gate" in workflow_ids
