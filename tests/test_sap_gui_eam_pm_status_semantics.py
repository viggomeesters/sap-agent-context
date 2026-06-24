from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-gui-eam-pm-status-semantics-pack.yaml"


def test_eam_pm_status_pack_contains_answer_contracts() -> None:
    ids = {item["id"] for item in yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]}
    assert "sap.pattern.eam.pm.ie03-status-navigation" in ids
    assert "sap.rule.eam.pm.ie03-display-vs-ie02-change" in ids
    assert "sap.rule.eam.pm-status-answer-contract" in ids
    assert "sap.pattern.eam.pm-equipment-status-profile-ddic" in ids


def test_ie03_status_dutch_query_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.navigation",
        topic="Waar zie ik in IE03 gebruiker statussen en systeem statussen equipment",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["status"] == "ready"
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.app.eam.pm.ie03" in selected
    assert "sap.pattern.eam.pm.ie03-status-navigation" in selected
    assert "sap.rule.eam.pm-status-answer-contract" in selected


def test_status_difference_query_is_ready_and_caveated() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.business_rules",
        topic="Wat is het verschil tussen system status en user status status profile",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["status"] == "ready"
    text = "\n".join(item["summary"] for item in bundle["items"]).lower()
    assert "system status" in text
    assert "user status" in text
    assert "status profile" in text
    assert "tenant verification" in text


def test_equipment_status_profile_ddic_query_is_ready_and_not_screen_field_led() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.field_mapping",
        topic="equipment status profile where stored JOSTD SSTXT TJ30T STSMA ESTAT",
        sap_product="cross_sap",
        limit=12,
    )
    assert bundle["status"] == "ready"
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.pattern.eam.pm-equipment-status-profile-ddic" in selected
    text = "\n".join(item["summary"] for item in bundle["items"]).lower()
    assert "jsto-stsma" in text
    assert "tj30t by estat alone" in text
    assert "jostd-sstxt" in text
    assert "not the durable storage table" in text
