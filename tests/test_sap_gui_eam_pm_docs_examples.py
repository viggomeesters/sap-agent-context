from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/sap-gui-eam-pm-queries.md"


def test_sap_gui_eam_pm_examples_exist_and_cover_prompt_questions() -> None:
    text = EXAMPLE.read_text(encoding="utf-8")
    for token in ["IE01", "IE02", "IE03", "IH08", "/n", "/o", "NIE01"]:
        assert token in text
    assert "system status" in text
    assert "user status" in text
    assert "status profile" in text
    assert "tenant-verification caveat" in text


def test_sap_gui_eam_pm_examples_preserve_public_boundary() -> None:
    text = EXAMPLE.read_text(encoding="utf-8").lower()
    for forbidden in ["https://tenant", "password", "secret_key", "client=", "customer name"]:
        assert forbidden not in text
    assert "must not require or include customer data" in text


def test_readme_links_sap_gui_eam_pm_examples() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "examples/sap-gui-eam-pm-queries.md" in readme
