from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/enterprise-process-backbone-bulk-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_enterprise_process_backbone_is_substantial() -> None:
    items = _items()
    assert len(items) >= 120
    kinds = {item["kind"] for item in items}
    required = {
        "external_reference",
        "sap_app",
        "sap_object",
        "sap_field",
        "field_map",
        "decision_rule",
        "test_pattern",
        "fo_pattern",
        "scope_item",
        "sap_role",
        "access_policy",
    }
    assert required <= kinds


def test_enterprise_process_backbone_items_are_fresh_and_source_labelled() -> None:
    for item in _items():
        assert item["freshness"]["review_after"] == "2026-12-23"
        assert item["freshness"]["expires_at"] == "2027-06-23"
        assert item["source"]["license_note"]
        assert item["claims"]
        assert item["access"] in {"public", "internal_derived"}
        if item["access"] == "public":
            assert item["source"]["url"].startswith("https://api.sap.com/api/")
            assert item["source"]["specificity"] == "catalog_entry"


def test_enterprise_process_backbone_retrieval_ready_for_specific_domains() -> None:
    loaded = load_items(ROOT)
    probes = [
        (
            "fo.field_mapping",
            "record to report journal entry period close general ledger profit center",
        ),
        (
            "fo.workflow",
            "outbound delivery picking goods issue delivery execution readiness",
        ),
        (
            "fo.test_scenarios",
            "production order mrp material confirmation manufacturing test pattern",
        ),
        (
            "fo.authorization",
            "maintenance order equipment business role catalog authorization",
        ),
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


def test_enterprise_process_backbone_generic_prompt_fails_closed() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.analytics",
        topic="generic enterprise dashboard everything report",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "needs_curation"
    assert bundle["gaps"]
