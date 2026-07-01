from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/sap-gui-eam-pm-queries.json"
OLD_EXAMPLE = ROOT / "examples/sap-gui-eam-pm-queries.md"


def test_sap_gui_eam_pm_examples_exist_and_cover_prompt_questions() -> None:
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    text = json.dumps(payload, sort_keys=True)
    assert payload["artifact_kind"] == "query_examples"
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
    assert not OLD_EXAMPLE.exists()


def test_readme_links_sap_gui_eam_pm_examples() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "examples/sap-gui-eam-pm-queries.json" in readme
    assert "examples/sap-gui-eam-pm-queries.md" not in readme
