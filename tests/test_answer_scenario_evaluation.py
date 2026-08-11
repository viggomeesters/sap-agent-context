from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.answer_scenario_evaluation import evaluate_answer_scenarios
from sap_agent_context.cli import main
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def _index_path(tmp_path: Path) -> Path:
    sqlite_path = tmp_path / "context.sqlite"
    build_indexes(
        load_items(ROOT),
        sqlite_path=sqlite_path,
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
    )
    return sqlite_path


def test_answer_scenario_fixtures_cover_concrete_to_vague_questions(tmp_path: Path) -> None:
    report = evaluate_answer_scenarios(root=ROOT, sqlite_path=_index_path(tmp_path))

    assert report["status"] == "passed"
    assert report["fixtures"] == 16
    ids = {result["id"] for result in report["results"]}
    assert {
        "concrete_mara_technical_fields",
        "concrete_mtart_field_description",
        "concrete_mtart_description_paraphrase_nl",
        "concrete_matnr_table_lookup",
        "concrete_matnr_table_lookup_paraphrase_nl",
        "concrete_vb42_cross_selling_package_tables",
        "concrete_hcm_personnel_name_employment_status",
        "mid_org_separation_nl",
        "mid_org_units_paraphrase_nl",
        "mid_org_units_inventory_nl",
        "mid_purchase_to_pay",
        "mid_procure_to_pay_paraphrase",
        "mid_integration_communication_security",
        "mid_analytics_extensibility_custom_field",
        "mid_procurement_release_strategy_workflow",
        "vague_sap_modules",
    } == ids


def test_answer_scenarios_preserve_live_web_boundary_and_external_evidence_hints(
    tmp_path: Path,
) -> None:
    report = evaluate_answer_scenarios(root=ROOT, sqlite_path=_index_path(tmp_path))

    assert "does not claim live internet validation" in report["contract"]["live_web_boundary"]
    by_id = {result["id"]: result for result in report["results"]}
    org = by_id["mid_org_separation_nl"]
    assert org["external_evidence_hints"]["required"] is True
    assert "learning.sap.com" in org["external_evidence_hints"]["accepted_domains"]
    assert org["citeable_results"] >= 1
    assert "sap_app" not in org["top_kinds"]

    modules = by_id["vague_sap_modules"]
    assert modules["expected_answer_status"] == "needs_curation"
    assert modules["status"] == "passed"


def test_answer_scenario_cli_outputs_json(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)
    exit_code = main(
        [
            "--root",
            str(ROOT),
            "evaluate-answer-scenarios",
            "--sqlite",
            str(sqlite_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact_kind"] == "answer_scenario_evaluation_report"
    assert payload["status"] == "passed"
