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
        "eam_pm_task_list_plan_fo_ready",
        "eam_pm_measuring_point_counter_fo_ready",
        "eam_pm_work_center_components_fo_ready",
        "eam_pm_confirmation_teco_settlement_fo_ready",
    } <= ids


def test_eam_pm_adversarial_queries_are_registered() -> None:
    data = yaml.safe_load((ROOT / "schema/adversarial-query-corpus.yaml").read_text())
    ids = {query["id"] for query in data["queries"]}
    assert "ambiguous_standalone_nie01_not_tcode" in ids
    assert "negative_tenant_specific_status_profile_values" in ids


def test_eam_pm_runtime_and_semantic_fixtures_are_registered() -> None:
    runtime = yaml.safe_load((ROOT / "schema/runtime-retrieval-fixtures.yaml").read_text())
    semantic = yaml.safe_load((ROOT / "schema/semantic-model-fixtures.yaml").read_text())
    runtime_ids = {fixture["id"] for fixture in runtime["fixtures"]}
    semantic_ids = {fixture["id"] for fixture in semantic["fixtures"]}

    assert {
        "eam_pm_task_list_plan_runtime",
        "eam_pm_measuring_point_counter_runtime",
        "eam_pm_confirmation_settlement_runtime",
    } <= runtime_ids
    assert {
        "nl_maintenance_plan_task_list",
        "en_measuring_point_counter",
        "nl_teco_settlement_caveat",
    } <= semantic_ids
