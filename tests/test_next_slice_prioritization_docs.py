from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "next-slice-prioritization.md"
GATES_DOC = ROOT / "docs" / "domain-density-gates.md"


def test_next_slice_prioritization_uses_measurable_non_filler_signals() -> None:
    text = DOC.read_text(encoding="utf-8")

    required = [
        "maturity-report",
        "gap-report",
        "Maturity gap",
        "Retrieval value",
        "FO risk",
        "Source availability",
        "Fixtureability",
        "Non-filler specificity",
        "Do not choose: too broad",
        "Analytics/extensibility candidate",
        "Integration security/API boundaries",
        "Procurement release strategy/workflow caveat",
        "Do not pick broad SAP filler as progress",
    ]
    for phrase in required:
        assert phrase in text


def test_domain_density_gates_link_next_slice_heuristic() -> None:
    text = GATES_DOC.read_text(encoding="utf-8")

    assert "next-slice-prioritization.md" in text
    assert "maturity-report" in text
    assert "gap-report" in text
    assert "without\nrewarding broad SAP filler" in text
