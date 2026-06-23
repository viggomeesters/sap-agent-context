from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/material-gui-navigation-pack.yaml"


def test_material_gui_navigation_pack_contains_required_tcodes() -> None:
    ids = {item["id"] for item in yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]}
    required = {
        "sap.app.material.mm01",
        "sap.app.material.mm02",
        "sap.app.material.mm03",
        "sap.app.material.mm60",
        "sap.app.material.mmbe",
        "sap.rule.material-gui-prefix-not-tcode",
    }
    assert required <= ids


def test_material_gui_navigation_query_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.navigation",
        topic="MM01 MM02 MM03 MM60 MMBE material transaction open search stock /n /o",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["status"] == "ready"
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.app.material.mm03" in selected
    assert "sap.app.material.mmbe" in selected
    assert "sap.rule.material-gui-prefix-not-tcode" in selected


def test_material_nmm03_query_does_not_treat_nmm03_as_tcode() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.navigation",
        topic="Welke transactie om material te openen NMM03 /nMM03",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    text = "\n".join(item["summary"] for item in bundle["items"]).lower()
    assert bundle["status"] == "ready"
    assert "nmm03 is not the transaction code" in text or "not a distinct nmm03" in text
