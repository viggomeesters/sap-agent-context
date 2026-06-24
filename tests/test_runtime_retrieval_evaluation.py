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
    assert report["fixtures"] >= 5
    ids = {result["id"] for result in report["results"]}
    assert "exact_transaction_ie03" in ids
    assert "semantic_display_equipment_master" in ids
    assert "evidence_citations_ie03_status" in ids


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
