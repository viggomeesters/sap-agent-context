from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/sdp-pattern-adoption-ledger.md"


def test_sdp_pattern_adoption_ledger_records_required_provenance() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    required = [
        "Provenance",
        "License",
        "copied_code",
        "ideas_extracted",
        "applied_in",
        "SSOT/read-model boundary",
        "Identity / alias / relation contracts",
        "Coverage classification",
    ]
    for marker in required:
        assert marker in text
    assert "copied_code=false" in text


def test_sdp_pattern_adoption_ledger_rejects_private_data_copying() -> None:
    text = LEDGER.read_text(encoding="utf-8").lower()
    forbidden_policy_markers = [
        "no customer/client names",
        "no project identifiers",
        "no xlsx contents",
        "no field-usage history",
        "no internal urls",
        "no secrets",
        "no proprietary mappings",
    ]
    for marker in forbidden_policy_markers:
        assert marker in text

    # Guard against accidentally copying obvious private/customer/project examples from SDP docs.
    forbidden_content_examples = [
        "prj-001",
        "prj-002",
        "hitachi",
        "kendrion",
        "swiss sense",
        "gemeente groningen",
        "universiteit utrecht",
    ]
    for marker in forbidden_content_examples:
        assert marker not in text


def test_sdp_pattern_adoption_ledger_preserves_sap_context_ssot_boundary() -> None:
    text = LEDGER.read_text(encoding="utf-8").lower()
    assert "canonical source of truth remains the yaml context" in text
    assert "generated db/json/sqlite/report artifacts are derived" in text
    assert "sap_fo_context_bundle" in text
