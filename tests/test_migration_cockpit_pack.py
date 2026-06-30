from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/migration-cockpit-template-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_migration_pack_has_required_context_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.field-atlas-migration-templates": "external_reference",
        "sap.ref.field-atlas-migration-relationships": "external_reference",
        "sap.app.migration-cockpit-template-review": "sap_app",
        "sap.app.migration-cockpit-simulation-review": "sap_app",
        "sap.object.migration-template": "sap_object",
        "sap.object.migration-project-run": "sap_object",
        "sap.object.migration-value-mapping": "sap_object",
        "sap.field-set.migration-template-core": "sap_field",
        "sap.field-set.migration-validation-results": "sap_field",
        "sap.field-set.migration-reconciliation": "sap_field",
        "sap.field-map.migration-source-target-template": "field_map",
        "sap.field-map.migration-value-source-transform": "field_map",
        "sap.field-map.product-number-template-verification": "field_map",
        "sap.field-set.migration-mapping-verification-evidence": "sap_field",
        "sap.field-map.migration-verified-mapping-ledger": "field_map",
        "sap.rule.ambiguous-migration-template-labels": "decision_rule",
        "sap.rule.migration-verified-mapping-ready-gate": "decision_rule",
        "sap.test-pattern.migration-template-validation": "test_pattern",
        "sap.test-pattern.migration-verified-mapping-gate": "test_pattern",
        "sap.test-pattern.migration-reconciliation-and-delta": "test_pattern",
    }

    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_migration_pack_preserves_ambiguous_label_caveats() -> None:
    items = _items_by_id()
    product_map = items["sap.field-map.product-number-template-verification"]
    rule = items["sap.rule.ambiguous-migration-template-labels"]

    assert product_map["field_map"][0]["confidence"] == "needs_verification"
    assert "needs_verification" in rule["summary"]
    outcomes = {outcome["outcome"] for outcome in rule["rules"]}
    assert "mark mapping needs_curation" in outcomes
    assert "mark mapping needs_verification and include verification note" in outcomes


def test_migration_public_items_are_link_first_and_freshness_labelled() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith(
                ("https://github.com/", "https://help.sap.com/")
            )
            license_note = item["source"]["license_note"]
            assert (
                "copy" in license_note
                or "MIT" in license_note
                or "do not mirror" in license_note
            )


def test_migration_verified_mapping_gate_requires_evidence_slots() -> None:
    items = _items_by_id()
    ledger = items["sap.field-map.migration-verified-mapping-ledger"]
    rule = items["sap.rule.migration-verified-mapping-ready-gate"]
    evidence_fields = items["sap.field-set.migration-mapping-verification-evidence"]

    targets = {step["target"] for step in ledger["mapping_steps"]}
    outcomes = {entry["outcome"] for entry in rule["rules"]}
    field_keys = {field["key"] for field in evidence_fields["field_definitions"]}

    assert "MappingEvidence.TemplateVersion" in targets
    assert "MappingEvidence.TransformAndValueSource" in targets
    assert "MappingEvidence.ValidationArtifact" in targets
    assert "not_ready_missing_validation_artifact" in outcomes
    assert "ready_with_tenant_caveat" in outcomes
    assert "MappingEvidence.ReadinessStatus" in field_keys


def test_migration_bundle_readiness_is_specific_not_ambiguous() -> None:
    items = load_items(ROOT)

    product_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="migration.analysis",
        topic="product number migration template target field verification",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    generic_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="migration.analysis",
        topic="migration template unknown label custom upload",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert product_bundle["status"] == "ready"
    assert any(
        item["id"] == "sap.field-map.product-number-template-verification"
        for item in product_bundle["items"]
    )
    assert generic_bundle["status"] == "needs_curation"
    assert any("Low topic precision" in gap for gap in generic_bundle["gaps"])
