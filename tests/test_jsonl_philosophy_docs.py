from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "jsonl-record-surface.md"
README = ROOT / "README.md"
RUNTIME_DOC = ROOT / "docs" / "local-runtime-index.md"
MIGRATION_DOC = ROOT / "docs" / "jsonl-migration-boundary.md"
TRUST_DOC = ROOT / "docs" / "retrieval-trust-boundary.md"
CONSUMER_DOC = ROOT / "docs" / "agent-consumer-contract.md"


def test_jsonl_record_surface_doc_names_alignment_and_deviations() -> None:
    text = DOC.read_text(encoding="utf-8")

    required_phrases = [
        "records-first",
        "records/*.jsonl is the canonical agent record surface",
        "YAML is a legacy authoring/import format",
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
    assert "docs/jsonl-migration-boundary.md" in text
    assert "docs/retrieval-trust-boundary.md" in text
    assert "validate-records --records-dir records" in text
    assert "records-first" in text
    assert "YAML is a legacy authoring/import format" in text


def test_runtime_doc_keeps_generated_runtime_and_future_migration_path_explicit() -> None:
    text = RUNTIME_DOC.read_text(encoding="utf-8")

    assert "records/*.jsonl" in text
    assert "build/context.sqlite" in text
    assert "generated/non-authoritative" in text
    assert "record_type" in text
    assert "sap_context_type" in text


def test_jsonl_migration_boundary_blocks_generated_artifact_authoring() -> None:
    text = MIGRATION_DOC.read_text(encoding="utf-8")

    required_phrases = [
        "records/*.jsonl` is the canonical agent-facing record surface",
        "validate-records --records-dir records",
        "YAML under `knowledge/**/*.yaml` is a legacy authoring/import format",
        "Do not hand-edit them",
        "Bulk import broad SAP content",
        "Mass-rename `kind`",
        "Weaken evaluation or completeness gates",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_retrieval_trust_boundary_keeps_consumer_claims_fail_closed() -> None:
    text = TRUST_DOC.read_text(encoding="utf-8")
    consumer = CONSUMER_DOC.read_text(encoding="utf-8")

    required_phrases = [
        "evidence-ranked context, not SAP product truth",
        "ready",
        "needs_curation",
        "report_only",
        "internal_derived",
        "source_ids",
        "claim_ids",
        "does not mean SAP Agent Context covers all SAP products",
    ]
    for phrase in required_phrases:
        assert phrase in text
    assert "records/*.jsonl`; `knowledge/**/*.yaml` is a legacy authoring/import path" in consumer
    assert "Retrieval trust boundary" in consumer
