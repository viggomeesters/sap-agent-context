from __future__ import annotations

from pathlib import Path

from sap_agent_context import cli
from sap_agent_context.semantic_model_evaluation import evaluate_semantic_models

ROOT = Path(__file__).resolve().parents[1]


def _fake_embeddings(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        if "ie03" in lowered or "equipment master" in lowered or "equipmentstam" in lowered:
            vectors.append([1.0, 0.0, 0.0])
        elif "user status" in lowered or "gebruikersstatus" in lowered:
            vectors.append([0.75, 0.25, 0.0])
        else:
            vectors.append([0.0, 1.0, 0.0])
    return vectors


def test_semantic_model_evaluation_covers_nl_and_en_fixtures_without_cloud(tmp_path: Path) -> None:
    fixtures_path = tmp_path / "semantic-fixtures.yaml"
    fixtures_path.write_text(
        """
fixtures:
  - id: nl_equipment_master_display
    language: nl
    query: Hoe toon ik equipmentstamgegevens in SAP?
    limit: 20
    filters:
      kind: sap_app
    required_ids:
      - sap.app.eam.pm.ie03
    require_vector_candidate: true
  - id: en_equipment_master_display
    language: en
    query: How do I display equipment master data?
    limit: 20
    filters:
      kind: sap_app
    required_ids:
      - sap.app.eam.pm.ie03
    require_vector_candidate: true
  - id: nl_equipment_status_meaning
    language: nl
    query: Wat betekent gebruikersstatus en systeemstatus bij equipment?
    limit: 30
    required_any:
      - - sap.object.eam-user-status
        - sap.claim.sap-object-eam-user-status.001
  - id: en_equipment_status_meaning
    language: en
    query: Explain equipment user status and system status
    limit: 30
    required_any:
      - - sap.object.eam-user-status
        - sap.claim.sap-object-eam-user-status.001
""".strip(),
        encoding="utf-8",
    )
    payload = evaluate_semantic_models(
        root=ROOT,
        sqlite_path=tmp_path / "context.sqlite",
        items_jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        fixtures_path=fixtures_path,
        models=["BAAI/bge-small-en-v1.5"],
        dimension=3,
        embed_texts=_fake_embeddings,
    )

    assert payload["status"] == "passed"
    assert payload["default_model"] == "BAAI/bge-small-en-v1.5"
    assert payload["recommended_default"] == "BAAI/bge-small-en-v1.5"
    assert payload["provider"] == "fastembed"
    assert payload["fixtures"] >= 4
    languages = {fixture["language"] for fixture in payload["results"][0]["fixtures"]}
    assert {"nl", "en"} <= languages
    assert "openai" not in str(payload).lower()
    assert "pinecone" not in str(payload).lower()


def test_semantic_model_evaluation_reports_failures_per_model(tmp_path: Path) -> None:
    def bad_embeddings(texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0, 0.0] for _ in texts]

    payload = evaluate_semantic_models(
        root=ROOT,
        sqlite_path=tmp_path / "context.sqlite",
        items_jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        models=["bad-local-model"],
        dimension=3,
        embed_texts=bad_embeddings,
    )

    assert payload["status"] == "failed"
    assert payload["results"][0]["status"] == "failed"
    assert payload["results"][0]["failures"]


def test_semantic_model_evaluation_cli_uses_default_fastembed_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_evaluate_semantic_models(**kwargs):
        assert kwargs["models"] == ["BAAI/bge-small-en-v1.5"]
        assert kwargs["provider"] == "fastembed"
        return {
            "status": "passed",
            "provider": "fastembed",
            "default_model": "BAAI/bge-small-en-v1.5",
            "recommended_default": "BAAI/bge-small-en-v1.5",
            "fixtures": 4,
            "results": [],
        }

    monkeypatch.setattr(cli, "evaluate_semantic_models", fake_evaluate_semantic_models)
    exit_code = cli.main(
        [
            "--root",
            str(ROOT),
            "evaluate-semantic-models",
            "--sqlite",
            str(tmp_path / "context.sqlite"),
            "--items-jsonl",
            str(tmp_path / "items.jsonl"),
            "--vector-jsonl",
            str(tmp_path / "vector-corpus.jsonl"),
        ]
    )

    assert exit_code == 0
