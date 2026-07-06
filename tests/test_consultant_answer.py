from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.cli import main
from sap_agent_context.consultant_answer import (
    _load_answer_profiles,
    evaluate_consultant_answers,
    generate_consultant_answer,
)
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


def test_consultant_answer_generates_prose_with_citations_and_boundaries(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="MTART omschrijving",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["artifact_kind"] == "sap_consultant_answer"
    assert answer["status"] == "ready"
    assert "MARA.MTART" in answer["answer"]
    assert "Material Type" in answer["answer"]
    assert "Artikelsoort" in answer["answer"]
    assert answer["citations"]
    assert answer["boundary"]["live_web_validation"] is False
    assert answer["boundary"]["expert_certification"] is False
    assert answer["boundary"]["tenant_specific_truth"] is False


def test_consultant_answer_fails_closed_for_generic_question(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="What is SAP?",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "needs_curation"
    assert answer["classification"] == "generic"
    assert "needs curation" in answer["answer"].lower()
    assert "intentionally narrow" in answer["answer"]


def test_consultant_answer_fails_closed_for_unsupported_tenant_config(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="How do I configure FI tax procedure for my tenant go-live?",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "needs_curation"
    assert answer["classification"] == "unsupported_configuration"
    assert "tenant/release/configuration-specific" in answer["answer"]


def test_consultant_answer_cli_rejects_zero_limit(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)
    try:
        main(
            [
                "--root",
                str(ROOT),
                "consultant-answer",
                "MTART omschrijving",
                "--sqlite",
                str(sqlite_path),
                "--limit",
                "0",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover - argparse should exit
        raise AssertionError("zero limit should fail argparse validation")
    assert "must be a positive integer" in capsys.readouterr().err


def test_consultant_answer_handles_vague_modules_as_needs_curation(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="Welke SAP modules zijn er?",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "needs_curation"
    assert "needs curation" in answer["answer"].lower()
    assert "complete module taxonomy" in answer["answer"]
    assert answer["citations"]



def test_consultant_answer_covers_integration_security(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question=(
            "Welke communicatie arrangement security checks en redactie zijn nodig "
            "zonder secrets of tenant URL?"
        ),
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "ready"
    assert answer["classification"] == "integration_security"
    assert "communication arrangement" in answer["answer"]
    assert "tenant URLs" in answer["answer"]
    assert "credentials" in answer["answer"]
    assert answer["citations"]


def test_consultant_answer_covers_analytics_extensibility(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question=(
            "Welke vragen moet ik stellen voor custom field exposure in analytics "
            "en API rapportage?"
        ),
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "ready"
    assert answer["classification"] == "analytics_extensibility"
    assert "custom-field" in answer["answer"]
    assert "exposure" in answer["answer"]
    assert "tenant-specific availability" in answer["answer"]
    assert answer["citations"]


def test_consultant_answer_covers_procurement_workflow(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="procurement release strategy flexible workflow threshold approver evidence",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "ready"
    assert answer["classification"] == "procurement_workflow"
    assert "release strategy" in answer["answer"]
    assert "approver" in answer["answer"]
    assert "tenant, release and customizing" in answer["answer"]
    assert answer["citations"]


def test_consultant_answer_keeps_generic_api_report_needs_curation(tmp_path: Path) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="How should API reporting work?",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "needs_curation"
    assert answer["classification"] == "generic"


def test_consultant_answer_keeps_generic_release_strategy_needs_curation(
    tmp_path: Path,
) -> None:
    answer = generate_consultant_answer(
        root=ROOT,
        question="What is release strategy?",
        sqlite_path=_index_path(tmp_path),
    )

    assert answer["status"] == "needs_curation"
    assert answer["classification"] == "generic"

def test_answer_profiles_fail_closed_on_invalid_required_citation(tmp_path: Path) -> None:
    profiles_path = tmp_path / "answer-profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "schema": "sap-agent-context.answer-profiles.v1",
                "artifact_kind": "answer_profiles",
                "profiles": [
                    {
                        "id": "broken",
                        "classification": "broken",
                        "status": "ready",
                        "support_ids": ["sap.example.support"],
                        "positive_fixture_ids": ["example_fixture"],
                        "adversarial_fixture_ids": [],
                        "required_answer_citation_ids": ["sap.example.missing"],
                        "curation_reason_required": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        _load_answer_profiles(profiles_path)
    except ValueError as exc:
        assert "citations outside support_ids" in str(exc)
    else:  # pragma: no cover - validation must fail closed
        raise AssertionError("invalid answer profile should fail validation")


def test_consultant_answer_evaluation_covers_all_answer_scenarios(tmp_path: Path) -> None:
    report = evaluate_consultant_answers(root=ROOT, sqlite_path=_index_path(tmp_path))

    assert report["artifact_kind"] == "consultant_answer_evaluation_report"
    assert report["status"] == "passed"
    assert report["fixtures"] == 14
    assert {result["status"] for result in report["results"]} == {"passed"}


def test_consultant_answer_cli_outputs_json(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)
    exit_code = main(
        [
            "--root",
            str(ROOT),
            "consultant-answer",
            "Hoe scheid je organisatie-eenheden in SAP?",
            "--sqlite",
            str(sqlite_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact_kind"] == "sap_consultant_answer"
    assert payload["status"] == "ready"
    assert "company code" in payload["answer"]
    assert "tenant" in payload["answer"]
    assert payload["citations"]


def test_consultant_answer_evaluation_cli_outputs_json(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)
    exit_code = main(
        [
            "--root",
            str(ROOT),
            "evaluate-consultant-answers",
            "--sqlite",
            str(sqlite_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact_kind"] == "consultant_answer_evaluation_report"
    assert payload["status"] == "passed"
    assert payload["fixtures"] == 14
