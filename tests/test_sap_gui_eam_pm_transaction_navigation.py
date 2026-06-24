from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-gui-eam-pm-transaction-navigation-pack.yaml"


def test_eam_pm_transaction_pack_contains_required_tcodes_and_prefix_rule() -> None:
    items = yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]
    ids = {item["id"] for item in items}
    required_apps = {
        "sap.app.eam.pm.ie01",
        "sap.app.eam.pm.ie02",
        "sap.app.eam.pm.ie03",
        "sap.app.eam.pm.ie05",
        "sap.app.eam.pm.ie06",
        "sap.app.eam.pm.il01",
        "sap.app.eam.pm.il02",
        "sap.app.eam.pm.il03",
        "sap.app.eam.pm.iw31",
        "sap.app.eam.pm.iw32",
        "sap.app.eam.pm.iw33",
        "sap.app.eam.pm.iw38",
        "sap.app.eam.pm.iw39",
        "sap.app.eam.pm.ih08",
        "sap.app.eam.pm.ih09",
        "sap.app.cross.migo",
        "sap.app.cross.mb51",
        "sap.app.cross.mm03",
    }
    assert required_apps <= ids
    assert "sap.rule.eam.pm.command-prefix-not-tcode" in ids
    text = PACK.read_text(encoding="utf-8").lower()
    assert "nie01 is not the transaction code" in text
    assert "mm03" in text
    assert "migo" in text
    assert "confidence: medium internal_derived" in text


def test_eam_pm_transaction_navigation_probe_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.navigation",
        topic="IE01 IE02 IE03 IH08 /n /o equipment transaction open search",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "ready"
    selected = {item["id"] for item in bundle["items"]}
    required_apps = {
        "sap.app.eam.pm.ie01",
        "sap.app.eam.pm.ie02",
        "sap.app.eam.pm.ie03",
        "sap.app.eam.pm.ih08",
    }
    assert required_apps <= selected
    assert "sap.rule.eam.pm.command-prefix-not-tcode" in selected


def test_eam_pm_nie01_query_does_not_treat_nie01_as_tcode() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.navigation",
        topic="Welke transacties om equipment te openen in SAP GUI NIE01 /nNIE01",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    text = "\n".join(item["summary"] for item in bundle["items"]).lower()
    assert bundle["status"] == "ready"
    assert "not the transaction code" in text or "not a distinct nie01" in text
