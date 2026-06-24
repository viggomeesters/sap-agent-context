from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def _build_vector_corpus(tmp_path: Path) -> list[dict]:
    build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
    )
    return [
        json.loads(line)
        for line in (tmp_path / "vector-corpus.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]


def test_vector_corpus_contains_item_and_claim_records(tmp_path: Path) -> None:
    records = _build_vector_corpus(tmp_path)
    ids = {record["id"] for record in records}

    assert "sap.app.eam.pm.ie03#summary" in ids
    assert "sap.claim.sap-app-eam-pm-ie03.001#statement" in ids
    assert len(records) > len(load_items(ROOT))


def test_item_vector_text_and_metadata_cover_retrieval_contract(tmp_path: Path) -> None:
    records = _build_vector_corpus(tmp_path)
    ie03 = next(record for record in records if record["id"] == "sap.app.eam.pm.ie03#summary")

    assert "IE03" in ie03["text"]
    assert "equipment" in ie03["text"].lower()
    assert "fo.navigation" in ie03["text"]
    assert ie03["metadata"]["canonical_record_id"] == "sap.app.eam.pm.ie03"
    assert ie03["metadata"]["kind"] == "sap_app"
    assert ie03["metadata"]["sap_product"] == "s4hana_cloud_public"
    assert ie03["metadata"]["source_path"]


def test_claim_vector_text_and_metadata_cover_evidence_context(tmp_path: Path) -> None:
    records = _build_vector_corpus(tmp_path)
    claim_id = "sap.claim.sap-app-eam-pm-ie03.001#statement"
    claim = next(record for record in records if record["id"] == claim_id)

    assert "IE03" in claim["text"]
    assert "evidence" in claim["text"].lower()
    assert "sap.ref.eam.pm.transaction-code-public-cross-check" in claim["text"]
    assert claim["metadata"]["canonical_record_id"] == "sap.claim.sap-app-eam-pm-ie03.001"
    assert claim["metadata"]["subject_id"] == "sap.app.eam.pm.ie03"
    assert claim["metadata"]["record_type"] == "claim"


def test_embedding_runtime_config_schema_is_local_first() -> None:
    schema = json.loads((ROOT / "schema/runtime-embedding-config.schema.json").read_text())
    providers = schema["properties"]["provider"]["enum"]

    assert {"fastembed", "sentence-transformers", "ollama", "custom-local"} <= set(providers)
    assert "pinecone" not in json.dumps(schema).lower()
    assert "openai" not in json.dumps(schema).lower()
