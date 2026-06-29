from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "context-bundle-consumer-contract.md"
CONSUMER_DOC = ROOT / "docs" / "agent-consumer-contract.md"


def test_context_bundle_consumer_contract_documents_required_fields_and_statuses() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    required = [
        "schema_version",
        "bundle_kind",
        "consumer_contract",
        "producer",
        "generated_at",
        "query",
        "status",
        "items",
        "citations",
        "gaps",
        "quality_signals",
        "ready",
        "needs_curation",
        "report_only is not a final bundle status",
        "source",
        "claims",
        "relations",
        "stale=true",
        "expired=true",
        "does not prove exhaustive SAP coverage",
    ]
    for phrase in required:
        assert phrase in text


def test_agent_consumer_contract_links_field_level_bundle_contract() -> None:
    text = CONSUMER_DOC.read_text(encoding="utf-8")

    assert "context-bundle-consumer-contract.md" in text
    assert "field-level JSON contract" in text
