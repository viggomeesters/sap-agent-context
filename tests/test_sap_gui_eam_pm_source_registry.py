from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-gui-eam-pm-source-registry-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_eam_pm_source_registry_has_public_gated_and_internal_labels() -> None:
    items = _items()
    access = {item["access"] for item in items}
    assert {"public", "gated", "internal_derived"} <= access
    assert any(item["id"] == "sap.rule.eam.pm.source-confidence-policy" for item in items)
    assert any(item["id"] == "sap.policy.eam.pm.public-boundary" for item in items)


def test_eam_pm_source_registry_is_link_first_and_has_freshness() -> None:
    for item in _items():
        assert item["freshness"]["review_after"]
        assert item["freshness"]["expires_at"]
        assert item["source"]["license_note"]
        if item["access"] in {"public", "gated"}:
            assert item["source"]["url"]
            note = item["source"]["license_note"].lower()
            assert "do not copy" in note or item["access"] == "gated"


def test_eam_pm_public_boundary_forbidden_terms_absent() -> None:
    text = PACK.read_text(encoding="utf-8").lower()
    # The policy may name forbidden data classes, but it must not contain actual examples/values.
    for marker in ["https://tenant", "client=", "password", "secret_key"]:
        assert marker not in text
    for term in ["customer", "equipment numbers", "internal urls", "exports"]:
        assert term in text
