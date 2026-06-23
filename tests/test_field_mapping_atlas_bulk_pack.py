from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/field-mapping-atlas-bulk-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_field_mapping_atlas_bulk_pack_is_substantial() -> None:
    items = _items()
    assert len(items) >= 80
    kinds = {item["kind"] for item in items}
    assert {"sap_field", "field_map", "decision_rule", "test_pattern"} <= kinds


def test_field_mapping_atlas_specific_probe_is_ready() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.field_mapping",
        topic="company code profit center segment controlling area mapping validation",
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "ready"
    selected_kinds = {item["kind"] for item in bundle["items"]}
    assert {"sap_field", "field_map", "decision_rule", "test_pattern"} <= selected_kinds


def test_field_mapping_atlas_generic_mapping_prompt_fails_closed() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.field_mapping",
        topic=(
            "map everything from legacy system to sap without source owner "
            "sample fields validation evidence"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert bundle["status"] == "needs_curation"
