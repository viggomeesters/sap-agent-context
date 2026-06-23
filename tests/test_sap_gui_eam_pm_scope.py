from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_sap_gui_eam_pm_scope_declared() -> None:
    matrix = yaml.safe_load((ROOT / "schema/completeness-matrix.yaml").read_text(encoding="utf-8"))
    domains = {domain["id"]: domain for domain in matrix["domains"]}
    assert "sap_gui_eam_pm" in domains
    domain = domains["sap_gui_eam_pm"]
    assert {"ie01", "ie02", "ie03", "ih08", "status"} <= set(domain["topic_tokens"])
    required = {"external_reference", "sap_app", "sap_object", "decision_rule", "test_pattern"}
    assert required <= set(domain["required_kinds"])


def test_sap_gui_eam_pm_starter_scope_doc_sets_public_boundary() -> None:
    text = (ROOT / "docs/sap-gui-eam-pm-starter-scope.md").read_text(encoding="utf-8")
    assert "`IE01` create equipment" in text
    assert "`IH08` equipment list/search" in text
    assert "not exhaustive SAP EAM/PM coverage" in text
    assert "internal_derived" in text
    assert "tenant-verification caveat" in text
