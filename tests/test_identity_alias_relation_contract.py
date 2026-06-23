from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schema/identity-alias-relation-contract.yaml"
DOC = ROOT / "docs/identity-alias-relation-contract.md"
LEDGER = ROOT / "docs/sdp-pattern-adoption-ledger.md"


def test_identity_alias_relation_contract_declares_ssot_and_derived_boundary() -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert data["source_of_truth"] == "yaml_context"
    assert data["provenance"]["copied_code"] is False
    assert data["provenance"]["copied_data"] is False
    assert "knowledge/**/*.yaml" in data["read_model_boundary"]["authoritative"]
    assert any("build/" in value for value in data["read_model_boundary"]["derived"])


def test_identity_alias_relation_contract_has_public_safe_rules() -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    alias_rules = "\n".join(data["contracts"]["aliases"]["rules"]).lower()
    relation_rules = "\n".join(data["contracts"]["relations"]["rules"]).lower()
    field_rules = "\n".join(data["contracts"]["field_identity"]["rules"]).lower()
    assert "customer" in alias_rules
    assert "project" in alias_rules
    assert "private/customer" in relation_rules
    assert "tenant-specific" in field_rules


def test_identity_alias_relation_contract_document_and_ledger_are_in_sync() -> None:
    doc = DOC.read_text(encoding="utf-8").lower()
    ledger = LEDGER.read_text(encoding="utf-8")
    assert "bundle_kind: sap_fo_context_bundle" in doc
    assert "generated read-model separation" in doc
    assert "schema/identity-alias-relation-contract.yaml" in ledger
    assert "docs/identity-alias-relation-contract.md" in ledger
