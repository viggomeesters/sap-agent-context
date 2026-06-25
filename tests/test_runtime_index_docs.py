from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_runtime_index_docs_cover_required_contracts() -> None:
    text = (ROOT / "docs/local-runtime-index.md").read_text(encoding="utf-8")
    status = (ROOT / "docs/runtime-index-status.md").read_text(encoding="utf-8")
    combined = text + "\n" + status + "\n" + (ROOT / "README.md").read_text(encoding="utf-8")

    required = [
        "records/*.jsonl",
        "generated runtime artifacts",
        "SQLite + FTS5",
        "sqlite-vec",
        "DuckDB",
        "not the primary runtime store",
        "fastembed",
        "sentence-transformers",
        "ollama",
        "runtime-search",
        "build-embeddings",
        "BAAI/bge-small-en-v1.5",
        "vector_embedding_records",
        "evaluate-runtime-retrieval",
        "evaluate-semantic-models",
        "NL/EN",
        "Do not add customer data",
        "internal URLs",
        "copied proprietary SAP documentation",
    ]
    missing = [needle for needle in required if needle not in combined]
    assert not missing


def test_agent_first_spec_names_runtime_index_boundary() -> None:
    text = (ROOT / "AGENT_FIRST_SPECIFICATION.md").read_text(encoding="utf-8")

    assert "build/context.sqlite" in text
    assert "records/*.jsonl` is the canonical agent record surface" in text
    assert "DuckDB is an optional analytics" in text
    assert "cloud\nvector dependencies must not be introduced" in text
