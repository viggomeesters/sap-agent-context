from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples/answer-proof-examples.md"


def _text() -> str:
    return EXAMPLES.read_text(encoding="utf-8")


def test_answer_proof_examples_cover_current_first_proof_slices() -> None:
    text = _text()

    required_sections = [
        "## Example 1 — Fiori app tracer answer",
        "## Example 2 — Verified Migration Cockpit mapping answer",
        "## Example 3 — Value-source/customizing answer",
        "## Example 4 — Local query/explain answer",
    ]
    for section in required_sections:
        assert section in text


def test_answer_proof_examples_cite_canonical_slice_items() -> None:
    text = _text()

    required_ids = [
        "sap.ref.fiori-apps-reference-library",
        "sap.field-map.fiori-app-traceability",
        "sap.field-map.migration-verified-mapping-ledger",
        "sap.rule.migration-verified-mapping-ready-gate",
        "sap.field-map.value-source-customizing-evidence",
        "sap.rule.value-source-customizing-ready-gate",
    ]
    for item_id in required_ids:
        assert item_id in text


def test_answer_proof_examples_fail_closed_on_tenant_specific_claims() -> None:
    text = _text()

    required_phrases = [
        "do not claim tenant availability",
        "not_ready_missing_validation_artifact",
        "needs_value_evidence",
        "not present it as tenant evidence",
        "Not allowed",
    ]
    for phrase in required_phrases:
        assert phrase in text
