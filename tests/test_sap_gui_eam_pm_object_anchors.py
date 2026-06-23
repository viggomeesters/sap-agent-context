from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/sap-gui-eam-pm-object-anchors-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_eam_pm_object_anchor_pack_distinguishes_status_objects() -> None:
    ids = {item["id"] for item in _items()}
    assert "sap.object.eam-equipment" in ids
    assert "sap.object.eam-system-status" in ids
    assert "sap.object.eam-user-status" in ids
    assert "sap.object.eam-status-profile" in ids
    text = PACK.read_text(encoding="utf-8").lower()
    assert "confidence: medium internal_derived" in text
    assert "tenant verification" in text


def test_eam_pm_object_anchor_status_probe_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.business_rules",
        topic="equipment system status user status status profile tenant verification",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "ready"
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.object.eam-equipment" in selected
    assert "sap.object.eam-system-status" in selected
    assert "sap.object.eam-user-status" in selected
    assert "sap.object.eam-status-profile" in selected
    assert "sap.rule.eam.pm.tenant-status-profile-caveat" in selected
