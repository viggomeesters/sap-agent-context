from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "downstream-consumer-fixtures.md"
CONTRACT_DOC = ROOT / "docs" / "context-bundle-consumer-contract.md"


def test_downstream_consumer_examples_cover_ready_curation_and_report_only() -> None:
    text = EXAMPLE.read_text(encoding="utf-8")

    required = [
        "Example A — ready bundle",
        "Example B — needs-curation bundle",
        "Example C — report_only slice",
        "Citations:",
        "Open questions:",
        "Needed before final output:",
        "target KPI names",
        "report-only coverage",
        "Anti-example — hallucinated tenant fact",
        "The bundle does not provide tenant-specific thresholds or role names",
    ]
    for phrase in required:
        assert phrase in text


def test_downstream_consumer_examples_do_not_embed_private_customer_facts() -> None:
    text = EXAMPLE.read_text(encoding="utf-8")

    forbidden = ["customer tenant", "client secret", "password", "Anne", "McCoy customer"]
    for phrase in forbidden:
        assert phrase.lower() not in text.lower()
    assert "Z_AP_MANAGER" in text  # explicitly marked unsafe/invented in anti-example


def test_bundle_contract_doc_links_downstream_examples() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "examples/downstream-consumer-fixtures.md" in text
    assert "anti-hallucination" in text
