from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/extensibility-analytics-pack.yaml"


def _items_by_id() -> dict[str, dict]:
    data = yaml.safe_load(PACK.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"]}


def test_extensibility_analytics_pack_has_required_shapes() -> None:
    items = _items_by_id()
    expected = {
        "sap.ref.s4hana-cloud-extensibility-help": "external_reference",
        "sap.ref.api-analytical-query-designer": "external_reference",
        "sap.app.custom-fields-and-logic-context": "sap_app",
        "sap.app-analytics-reporting-context": "sap_app",
        "sap.object.custom-field-extension": "sap_object",
        "sap.object.analytics-query": "sap_object",
        "sap.field-set.custom-field-lifecycle-core": "sap_field",
        "sap.field-set.analytics-query-core": "sap_field",
        "sap.field-map.custom-field-exposure-readiness": "field_map",
        "sap.field-map.analytics-report-readiness": "field_map",
        "sap.rule.custom-field-tenant-boundary": "decision_rule",
        "sap.rule.analytics-reporting-readiness": "decision_rule",
        "sap.test-pattern.extensibility-analytics-readiness": "test_pattern",
        "sap.pattern.extensibility.custom-field-fo": "fo_pattern",
        "sap.pattern.analytics.reporting-fo": "fo_pattern",
        "sap.rule.custom-field-report-exposure-fail-closed": "decision_rule",
        "sap.rule.analytics-kpi-source-fail-closed": "decision_rule",
        "sap.test-pattern.custom-field-exposure-regression": "test_pattern",
        "sap.test-pattern.analytics-report-filter-freshness": "test_pattern",
    }
    for item_id, kind in expected.items():
        assert items[item_id]["kind"] == kind


def test_custom_field_tenant_boundary_and_analytics_readiness_are_explicit() -> None:
    items = _items_by_id()
    custom_rule = items["sap.rule.custom-field-tenant-boundary"]
    analytics_rule = items["sap.rule.analytics-reporting-readiness"]
    custom_targets = {
        step["target"]
        for step in items["sap.field-map.custom-field-exposure-readiness"]["mapping_steps"]
    }
    analytics_targets = {
        step["target"]
        for step in items["sap.field-map.analytics-report-readiness"]["mapping_steps"]
    }

    assert any("tenant-context" in rule["outcome"] for rule in custom_rule["rules"])
    assert any("needs-curation" in rule["outcome"] for rule in analytics_rule["rules"])
    assert "CustomField.APIExposure" in custom_targets
    assert "CustomField.PublishStatus" in custom_targets
    assert "AnalyticsQuery.Filter" in analytics_targets
    assert "AnalyticsQuery.DataFreshness" in analytics_targets


def test_extensibility_analytics_public_items_are_source_and_freshness_labelled() -> None:
    for item in _items_by_id().values():
        assert str(item["freshness"]["review_after"]) == "2026-12-23"
        assert str(item["freshness"]["expires_at"]) == "2027-06-23"
        if item["access"] == "public":
            assert item["source"]["url"].startswith(("https://help.sap.com/", "https://api.sap.com/"))
            license_note = item["source"]["license_note"].lower()
            assert "copy" in license_note or "link-first" in license_note


def test_extensibility_analytics_bundle_readiness_is_specific_not_generic() -> None:
    items = load_items(ROOT)
    bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.field_mapping",
        topic=(
            "custom field business context api exposure publish status "
            "analytics query kpi filter data freshness"
        ),
        sap_product="s4hana_cloud_public",
        limit=12,
    )
    generic_bundle = build_context_bundle(
        items,
        root=ROOT,
        intent="fo.analytics",
        topic="generic executive dashboard performance report",
        sap_product="s4hana_cloud_public",
        limit=12,
    )

    assert bundle["status"] == "ready"
    selected_ids = {item["id"] for item in bundle["items"]}
    assert "sap.field-map.custom-field-exposure-readiness" in selected_ids
    assert "sap.field-map.analytics-report-readiness" in selected_ids
    assert "sap.test-pattern.extensibility-analytics-readiness" in selected_ids
    assert generic_bundle["status"] == "needs_curation"
    assert any("Low topic precision" in gap for gap in generic_bundle["gaps"])


def test_extensibility_analytics_deep_slice_follows_template_dimensions() -> None:
    items = _items_by_id()

    fo_patterns = [item for item in items.values() if item["kind"] == "fo_pattern"]
    assert {item["id"] for item in fo_patterns} == {
        "sap.pattern.extensibility.custom-field-fo",
        "sap.pattern.analytics.reporting-fo",
    }
    for pattern in fo_patterns:
        assert pattern["required_questions"]
        assert pattern["assumptions"]
        assert pattern["non_goals"]
        assert pattern["validation_notes"]

    fail_closed_rules = {
        "sap.rule.custom-field-report-exposure-fail-closed",
        "sap.rule.analytics-kpi-source-fail-closed",
    }
    for item_id in fail_closed_rules:
        rules = items[item_id]["rules"]
        assert all({"if", "then", "outcome"} <= set(rule) for rule in rules)
        assert any("ask" in rule["then"] or "block" in rule["then"] for rule in rules)


def test_extensibility_analytics_eval_and_runtime_fixtures_cover_new_slice() -> None:
    fo = yaml.safe_load((ROOT / "schema/fo-output-evaluation-fixtures.yaml").read_text())
    runtime = yaml.safe_load((ROOT / "schema/runtime-retrieval-fixtures.yaml").read_text())
    semantic = yaml.safe_load((ROOT / "schema/semantic-model-fixtures.yaml").read_text())

    fo_fixture = {fixture["id"]: fixture for fixture in fo["fixtures"]}[
        "extensibility_analytics_ready"
    ]
    assert "fo_pattern" in fo_fixture["required_kinds"]
    assert {
        "sap.pattern.extensibility.custom-field-fo",
        "sap.pattern.analytics.reporting-fo",
        "sap.rule.custom-field-report-exposure-fail-closed",
        "sap.rule.analytics-kpi-source-fail-closed",
    } <= set(fo_fixture["required_item_ids"])

    runtime_ids = {fixture["id"] for fixture in runtime["fixtures"]}
    assert {
        "analytics_extensibility_custom_field_runtime",
        "analytics_reporting_kpi_runtime",
    } <= runtime_ids

    semantic_ids = {fixture["id"] for fixture in semantic["fixtures"]}
    assert {
        "nl_custom_field_analytics_exposure",
        "en_analytics_kpi_filter_freshness",
    } <= semantic_ids
