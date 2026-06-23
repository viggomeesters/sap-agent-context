from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/material-etm-starter-scope.md"


def test_material_etm_scope_declares_bounded_subjects() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in ["Material / Product Master", "EAM material links", "ETM"]:
        assert token in text
    for token in ["MM01", "MM02", "MM03", "MM60", "MMBE", "/n"]:
        assert token in text
    assert "Equipment and Tools Management" in text
    assert "acronym needs clarification" in text


def test_material_etm_scope_preserves_public_boundary() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    assert "do not claim exhaustive" in text or "does not claim exhaustive" in text
    assert "customer equipment/material numbers" in text
    assert "copied sap documentation" in text
    assert "tenant-verification caveats" in text or "tenant verification caveats" in text
