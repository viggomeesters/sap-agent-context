from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schema/field-atlas-absorption-contract.yaml"


def test_field_atlas_absorption_contract_covers_all_source_concepts() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    assert contract["provenance_source"]["repo"] == "viggomeesters/sap-field-atlas"
    assert contract["provenance_source"]["status"] == "archived_public_legacy_seed"
    assert contract["policy"]["runtime_dependency"] is False
    assert contract["policy"]["import_package"] is False
    assert contract["policy"]["copy_standalone_cli"] is False
    assert contract["policy"]["copy_standalone_schemas"] is False
    assert contract["policy"]["copy_generated_artifacts"] is False

    assert set(contract["concept_mappings"]) == {
        "transactions",
        "tables",
        "fields",
        "domains_value_sources",
        "relationships",
        "migration_templates",
        "fiori_apps",
    }


def test_field_atlas_absorption_contract_routes_concepts_to_canonical_items() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    mappings = contract["concept_mappings"]

    assert "sap_app" in mappings["transactions"]["canonical_kinds"]
    assert "sap_object" in mappings["tables"]["canonical_kinds"]
    assert "sap_field" in mappings["fields"]["canonical_kinds"]
    assert "field_map" in mappings["fields"]["canonical_kinds"]
    assert "decision_rule" in mappings["domains_value_sources"]["canonical_kinds"]
    assert "relations" not in mappings["relationships"].get("canonical_kinds", [])
    assert "field_map" in mappings["migration_templates"]["canonical_kinds"]
    assert "sap_role" in mappings["fiori_apps"]["canonical_kinds"]
    assert "access_policy" in mappings["fiori_apps"]["canonical_kinds"]


def test_field_atlas_contract_is_linked_from_docs_and_layout() -> None:
    docs = (ROOT / "docs/field-atlas-integration.md").read_text(encoding="utf-8")
    layout = yaml.safe_load((ROOT / "schema/context-layout.yaml").read_text(encoding="utf-8"))

    assert "schema/field-atlas-absorption-contract.yaml" in docs
    assert "archived public legacy/provenance seed" in docs
    assert (
        layout["import_policy"]["field_atlas_contract"]
        == "schema/field-atlas-absorption-contract.yaml"
    )
