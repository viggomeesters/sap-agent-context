from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "schema/coverage-classification-model.yaml"
DOC = ROOT / "docs/coverage-classification-model.md"
LEDGER = ROOT / "docs/sdp-pattern-adoption-ledger.md"


def test_coverage_classification_model_has_required_statuses() -> None:
    data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))
    assert data["provenance"]["copied_code"] is False
    assert data["provenance"]["copied_data"] is False
    assert set(data["statuses"]) == {
        "ready",
        "needs_curation",
        "source_gap",
        "tenant_verification_required",
        "no_source_known",
    }


def test_coverage_classification_model_blocks_fake_green() -> None:
    data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))
    rules = {rule["then"]: rule["if"] for rule in data["classification_rules"]}
    assert "acceptable evidence is missing" in rules["source_gap"]
    assert "tenant/live-system" in rules["tenant_verification_required"]
    assert "freshness" in rules["needs_curation"]
    assert "required gates pass" in rules["ready"]


def test_coverage_classification_doc_and_ledger_are_in_sync() -> None:
    doc = DOC.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")
    statuses = [
        "ready",
        "needs_curation",
        "source_gap",
        "tenant_verification_required",
        "no_source_known",
    ]
    for status in statuses:
        assert status in doc
    assert "schema/coverage-classification-model.yaml" in ledger
    assert "docs/coverage-classification-model.md" in ledger
