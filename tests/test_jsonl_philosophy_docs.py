from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "jsonl-record-surface.md"
README = ROOT / "README.md"
RUNTIME_DOC = ROOT / "docs" / "local-runtime-index.md"


def test_jsonl_record_surface_doc_names_alignment_and_deviations() -> None:
    text = DOC.read_text(encoding="utf-8")

    required_phrases = [
        "records-first",
        "YAML remains the temporary editing source",
        "records/*.jsonl is the deterministic agent-first record surface",
        "build/ is generated runtime output",
        "Intentional deviations",
        "record_type",
        "sap_context_type",
        "items.jsonl",
        "`kind` is a compatibility field",
        "Do not model one YAML file or Markdown note as one JSONL line",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_readme_links_jsonl_record_surface_decision() -> None:
    text = README.read_text(encoding="utf-8")

    assert "docs/jsonl-record-surface.md" in text
    assert "records-first" in text
    assert "YAML knowledge stays green" in text


def test_runtime_doc_keeps_generated_runtime_and_future_migration_path_explicit() -> None:
    text = RUNTIME_DOC.read_text(encoding="utf-8")

    assert "records/*.jsonl" in text
    assert "build/context.sqlite" in text
    assert "generated/non-authoritative" in text
    assert "record_type" in text
    assert "sap_context_type" in text
