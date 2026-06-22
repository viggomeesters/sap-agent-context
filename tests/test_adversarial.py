from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path

import yaml

from sap_fo_knowledge_base.bundle import build_context_bundle
from sap_fo_knowledge_base.completeness import audit_completeness
from sap_fo_knowledge_base.model import KnowledgeItem
from sap_fo_knowledge_base.repository import load_items
from sap_fo_knowledge_base.validation import has_errors, validate_items

ROOT = Path(__file__).resolve().parents[1]


def test_audit_fails_when_required_kind_is_removed() -> None:
    items = [item for item in load_items(ROOT) if item.kind != "test_pattern"]

    report = audit_completeness(items, root=ROOT, current_date=date(2026, 6, 22))

    assert report["status"] == "failed"
    assert report["critical"] > 0 or report["important"] > 0


def test_audit_fails_when_domain_has_too_few_items() -> None:
    items = [
        item
        for item in load_items(ROOT)
        if not {"procurement", "purchase", "requisition"}.intersection(item.topics)
    ]

    report = audit_completeness(items, root=ROOT, current_date=date(2026, 6, 22))

    assert report["status"] == "failed"
    assert any(finding["area"] == "domain:procurement" for finding in report["findings"])


def test_bundle_with_only_generic_source_pointer_is_not_ready() -> None:
    items = [
        item
        for item in load_items(ROOT)
        if item.kind == "external_reference" and "sap-help" in item.topics
    ]

    bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.workflow",
        topic="supplier invoice workflow",
        sap_product="s4hana_cloud_public",
        limit=5,
        current_date=date(2026, 6, 22),
    )

    assert bundle["status"] == "needs_curation"
    assert bundle["gaps"]


def test_unknown_topic_does_not_return_intent_only_bundle() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.integration",
        topic="walnoot onbekend nonsense",
        sap_product="s4hana_cloud_public",
        limit=8,
        current_date=date(2026, 6, 22),
    )

    assert bundle["status"] == "needs_curation"
    assert bundle["items"] == []


def test_dutch_english_mixed_query_returns_usable_companion_bundle() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.workflow",
        topic="factuur goedkeuring AP leveranciers invoice approval",
        sap_product="s4hana_cloud_public",
        limit=12,
        current_date=date(2026, 6, 22),
    )

    kinds = {item["kind"] for item in bundle["items"]}
    assert bundle["status"] == "ready"
    assert {"external_reference", "sap_app", "sap_object", "field_map", "test_pattern"}.issubset(
        kinds
    )
    assert bundle["gaps"] == []


def test_gated_item_with_false_login_flag_fails_validation() -> None:
    item = next(item for item in load_items(ROOT) if item.access == "gated")
    payload = deepcopy(item.data)
    payload["requires_login"] = False
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("gated sources must set requires_login" in issue.message for issue in issues)


def test_public_item_with_internal_source_kind_fails_validation() -> None:
    item = next(item for item in load_items(ROOT) if item.access == "public")
    payload = deepcopy(item.data)
    payload["source"]["kind"] = "internal_pattern"
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("does not match access" in issue.message for issue in issues)


def test_public_item_with_internal_derived_evidence_fails_validation() -> None:
    items = load_items(ROOT)
    public_item = next(item for item in items if item.item_id == "sap.app.manage-sales-orders")
    internal_item = next(item for item in items if item.access == "internal_derived")
    payload = deepcopy(public_item.data)
    payload["claims"][0]["evidence"] = [internal_item.item_id]
    mutated = KnowledgeItem(path=public_item.path, data=payload)

    issues = validate_items([mutated, internal_item], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("public item uses internal-derived evidence" in issue.message for issue in issues)


def test_missing_claim_evidence_id_fails_validation() -> None:
    item = next(item for item in load_items(ROOT) if item.item_id == "sap.object.sales-order")
    payload = deepcopy(item.data)
    payload["claims"][0]["evidence"] = ["sap.missing.evidence"]
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("is not a known item id or URL" in issue.message for issue in issues)


def test_missing_relation_id_fails_validation() -> None:
    item = next(item for item in load_items(ROOT) if item.item_id == "sap.object.sales-order")
    payload = deepcopy(item.data)
    payload.setdefault("relations", {})["objects"] = ["sap.object.missing"]
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("relations.objects references missing item" in issue.message for issue in issues)


def test_generic_root_source_fails_when_high_specificity_is_required() -> None:
    item = next(
        item for item in load_items(ROOT) if item.item_id == "sap.ref.s4hana-cloud-help-portal"
    )
    payload = deepcopy(item.data)
    payload["requires_source_specificity"] = "high"
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert has_errors(issues)
    assert any("generic root source URL" in issue.message for issue in issues)


def test_exact_source_satisfies_high_specificity_requirement() -> None:
    item = next(
        item for item in load_items(ROOT) if item.item_id == "sap.ref.s4hana-cloud-help-portal"
    )
    payload = deepcopy(item.data)
    payload["requires_source_specificity"] = "high"
    payload["source"]["url"] = "https://help.sap.com/docs/SAP_S4HANA_CLOUD/example/exact-topic"
    payload["source"]["specificity"] = "exact_page"
    payload["claims"][0]["evidence"] = [payload["source"]["url"]]
    payload["relations"] = {}
    mutated = KnowledgeItem(path=item.path, data=payload)

    issues = validate_items([mutated], current_date=date(2026, 6, 22))

    assert not has_errors(issues), [issue.to_dict() for issue in issues]


def test_stale_items_make_bundle_needs_curation() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.workflow",
        topic="supplier invoice workflow",
        sap_product="s4hana_cloud_public",
        limit=12,
        current_date=date(2027, 1, 1),
    )

    assert bundle["status"] == "needs_curation"
    assert any("past review_after" in gap for gap in bundle["gaps"])


def test_adversarial_query_corpus_expected_statuses() -> None:
    corpus = yaml.safe_load((ROOT / "schema/adversarial-query-corpus.yaml").read_text())
    items = load_items(ROOT)

    for query in corpus["queries"]:
        bundle = build_context_bundle(
            items,
            root=ROOT,
            intent=query["intent"],
            topic=query["topic"],
            sap_product=query["sap_product"],
            limit=query["limit"],
            current_date=date(2026, 6, 22),
        )
        assert bundle["status"] == query["expected_status"], query["id"]
        expected_gap = query.get("expected_gap_contains")
        if expected_gap:
            assert any(expected_gap in gap for gap in bundle["gaps"]), query["id"]
