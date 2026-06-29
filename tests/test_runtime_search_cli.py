from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.cli import main
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

ROOT = Path(__file__).resolve().parents[1]


def _index_path(tmp_path: Path) -> Path:
    sqlite_path = tmp_path / "context.sqlite"
    build_indexes(
        load_items(ROOT),
        sqlite_path=sqlite_path,
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector.jsonl",
        root=ROOT,
    )
    return sqlite_path


def test_runtime_search_filters_kind_access_topic_and_used_for(tmp_path: Path) -> None:
    results = search_runtime_index(
        _index_path(tmp_path),
        "IE03 equipment display",
        limit=8,
        kind="sap_app",
        access="internal_derived",
        topic="ie03",
        used_for="fo.navigation",
    )

    assert results[0]["id"] == "sap.app.eam.pm.ie03"
    assert all(result["kind"] in {"sap_app", "claim"} for result in results)
    assert results[0]["claim_ids"]
    assert results[0]["source_ids"]


def test_runtime_search_output_is_citeable_for_bundle_generation(tmp_path: Path) -> None:
    results = search_runtime_index(_index_path(tmp_path), "IE03 equipment status", limit=5)
    top = results[0]

    assert top["id"] == "sap.app.eam.pm.ie03"
    assert top["claim_ids"]
    assert top["source_ids"]
    assert {"id", "score", "source", "text", "claim_ids", "source_ids", "explain"} <= set(top)


def test_runtime_search_explains_ranking_source_terms_and_evidence(tmp_path: Path) -> None:
    results = search_runtime_index(_index_path(tmp_path), "IE03 equipment status", limit=5)
    explain = results[0]["explain"]

    assert explain["rank_source"] in {"item_fts", "item_exact"}
    assert "IE03" in explain["matched_terms"]
    assert "equipment" in explain["matched_terms"]
    assert explain["exact_token_hits"] >= 1
    assert explain["source_ids"]
    assert explain["claim_ids"]
    assert explain["access"] in {"public", "gated", "internal_derived"}
    assert explain["freshness"]["review_after"]


def test_runtime_search_cli_outputs_json(tmp_path: Path, capsys) -> None:
    sqlite_path = _index_path(tmp_path)

    exit_code = main(
        [
            "--root",
            str(ROOT),
            "runtime-search",
            "IE03 equipment display",
            "--sqlite",
            str(sqlite_path),
            "--kind",
            "sap_app",
            "--limit",
            "3",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"
    assert payload["query"] == "IE03 equipment display"
    assert payload["results"][0]["id"] == "sap.app.eam.pm.ie03"
    assert payload["results"][0]["explain"]["source_ids"]
