from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/api-event-surface-bulk-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_api_event_surface_bulk_pack_is_substantial() -> None:
    items = _items()
    assert len(items) >= 90
    ids = {item["id"] for item in items}
    assert "sap.bulk.api.sales-order.ref" in ids
    assert "sap.bulk.api.bp.field-map" in ids
    assert "sap.bulk.api.analytical-query.test-pattern" in ids


def test_api_event_surface_public_items_are_link_first() -> None:
    for item in _items():
        assert item["freshness"]["review_after"] == "2026-12-23"
        assert item["freshness"]["expires_at"] == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert "do not copy" in item["source"]["license_note"].lower()
        assert "tenant hostnames" not in item["summary"].lower()


def test_api_event_surface_specific_probes_are_ready() -> None:
    loaded = load_items(ROOT)
    probes = [
        ("fo.field_mapping", "sales order api payload business key lifecycle status"),
        ("fo.field_mapping", "bp api role category search term payload"),
        ("fo.test_scenarios", "inspection lot api usage decision quality test pattern"),
    ]
    for intent, topic in probes:
        bundle = build_context_bundle(
            loaded,
            root=ROOT,
            intent=intent,
            topic=topic,
            sap_product="s4hana_cloud_public",
            limit=12,
        )
        assert bundle["bundle_kind"] == "sap_fo_context_bundle"
        assert bundle["status"] == "ready"
        assert bundle["quality_signals"]["source_url_count"] >= 1


def test_existing_integration_security_policy_still_wins_top_12() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.integration",
        topic=(
            "integration api communication arrangement credentials tenant url "
            "payload business key error handling no secrets"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    selected = {item["id"] for item in bundle["items"]}
    assert "sap.policy.integration-no-secrets" in selected
    assert bundle["status"] == "ready"
