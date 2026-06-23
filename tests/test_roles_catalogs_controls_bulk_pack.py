from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/roles-catalogs-controls-bulk-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_roles_controls_bulk_pack_is_substantial_and_synthetic() -> None:
    items = _items()
    assert len(items) >= 80
    kinds = {item["kind"] for item in items}
    assert {"sap_role", "decision_rule", "test_pattern", "access_policy"} <= kinds
    text = yaml.safe_dump(items).lower()
    assert "real identity values" in text
    assert "tenant permission profile" in text
    assert "screenshots" in text


def test_roles_controls_specific_access_probe_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.authorization",
        topic="payment proposal reviewer segregation approval boundary negative identity",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "ready"
    selected_kinds = {item["kind"] for item in bundle["items"]}
    assert {"sap_role", "access_policy", "decision_rule", "test_pattern"} <= selected_kinds


def test_canonical_authorization_caveat_still_selected() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.authorization",
        topic="authorization business role catalog restriction test user access caveat",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.policy.authorization-tenant-verification" in selected
    assert "sap.rule.authorization-access-caveat" in selected
    assert bundle["status"] == "ready"
