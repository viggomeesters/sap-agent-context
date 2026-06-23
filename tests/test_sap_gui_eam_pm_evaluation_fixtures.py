from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_eam_pm_fixtures_are_registered() -> None:
    data = yaml.safe_load((ROOT / "schema/fo-output-evaluation-fixtures.yaml").read_text())
    ids = {fixture["id"] for fixture in data["fixtures"]}
    assert {
        "sap_gui_eam_pm_equipment_transactions_ready",
        "sap_gui_eam_pm_ie03_status_ready",
        "sap_gui_eam_pm_status_difference_ready",
        "sap_gui_eam_pm_equipment_search_ready",
    } <= ids


def test_eam_pm_adversarial_queries_are_registered() -> None:
    data = yaml.safe_load((ROOT / "schema/adversarial-query-corpus.yaml").read_text())
    ids = {query["id"] for query in data["queries"]}
    assert "ambiguous_standalone_nie01_not_tcode" in ids
    assert "negative_tenant_specific_status_profile_values" in ids
