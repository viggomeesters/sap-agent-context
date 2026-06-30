from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.cli import main
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_evaluation import evaluate_runtime_retrieval

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


def test_runtime_retrieval_fixtures_pass(tmp_path: Path) -> None:
    report = evaluate_runtime_retrieval(root=ROOT, sqlite_path=_index_path(tmp_path))

    assert report["status"] == "passed"
    assert report["fixtures"] >= 18
    ids = {result["id"] for result in report["results"]}
    assert "exact_transaction_ie03" in ids
    assert "semantic_display_equipment_master" in ids
    assert "evidence_citations_ie03_status" in ids
    assert "focused_procurement_decision_rule_runtime" in ids
    assert "focused_integration_error_retry_pattern_runtime" in ids
    assert "focused_integration_error_retry_rule_runtime" in ids
    assert "adversarial_generic_dashboard_not_ready" in ids
    assert "adversarial_invented_tenant_field_not_authoritative" in ids
    assert "adversarial_unrelated_hr_payroll_module_no_eam_ready_context" in ids
    assert "foundation_context_from_zero_runtime" in ids
    assert "alias_evolution_ltmc_runtime" in ids
    assert "source_registry_access_boundary_runtime" in ids
    assert "adversarial_roadmap_not_delivery_proof_runtime" in ids


def test_runtime_retrieval_fixture_schema_supports_adversarial_forbidden_ids(
    tmp_path: Path,
) -> None:
    sqlite_path = _index_path(tmp_path)
    fixture_path = tmp_path / "adversarial-fixtures.yaml"
    fixture_path.write_text(
        """
fixtures:
  - id: forced_forbidden_id_failure
    query: IE03 equipment display
    limit: 5
    forbidden_ids:
      - sap.app.eam.pm.ie03
""",
        encoding="utf-8",
    )

    report = evaluate_runtime_retrieval(
        root=ROOT,
        sqlite_path=sqlite_path,
        fixtures_path=fixture_path,
    )

    assert report["status"] == "failed"
    assert "forbidden id present" in report["results"][0]["failures"][0]


def test_runtime_retrieval_cli_outputs_json(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)
    exit_code = main(
        [
            "--root",
            str(ROOT),
            "evaluate-runtime-retrieval",
            "--sqlite",
            str(sqlite_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"
