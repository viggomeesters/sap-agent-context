from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RETRO = ROOT / "schema/deep-slice-retro-gate.yaml"
DOC = ROOT / "docs/deep-slice-retro-gate.md"


def _retro_gate() -> dict:
    return yaml.safe_load(RETRO.read_text(encoding="utf-8"))


def test_deep_slice_retro_gate_checks_multiple_non_eam_slices() -> None:
    gate = _retro_gate()
    checked = [slice_ for slice_ in gate["slices"] if slice_["status"] == "checked"]
    checked_ids = {slice_["id"] for slice_ in checked}

    assert "analytics_extensibility" in checked_ids
    assert "integration_security" in checked_ids
    assert "procurement_release_strategy" in checked_ids
    assert len([slice_ for slice_ in checked if slice_["id"] != "eam_pm_lifecycle"]) >= 2


def test_deep_slice_retro_gate_covers_template_dimensions_and_followups() -> None:
    gate = _retro_gate()
    dimensions = set(gate["template_dimensions"])

    for slice_ in gate["slices"]:
        statuses = slice_["dimension_status"]
        assert set(statuses) == dimensions
        assert all(value in {"met", "follow_up", "no_follow_up"} for value in statuses.values())
        assert slice_["follow_up"]["status"] in {"none", "follow_up", "no_follow_up"}
        assert slice_["follow_up"]["reason"].strip()


def test_deep_slice_retro_gate_documents_no_exhaustive_coverage_claim() -> None:
    doc = DOC.read_text(encoding="utf-8")
    gate = _retro_gate()

    assert "not exhaustive SAP coverage" in doc
    assert "procurement_release_strategy" in doc
    assert gate["description"].startswith("Retro gate")
