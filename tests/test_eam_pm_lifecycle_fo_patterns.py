from __future__ import annotations

from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge/domain-packs/eam-pm-lifecycle-fo-patterns-pack.yaml"


def _items() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))["items"]


def test_eam_pm_lifecycle_fo_patterns_cover_major_slices() -> None:
    items = _items()
    fo_ids = {item["id"] for item in items if item["kind"] == "fo_pattern"}
    rule_ids = {item["id"] for item in items if item["kind"] == "decision_rule"}

    assert {
        "sap.pattern.eam.pm-equipment-foundation-fo",
        "sap.pattern.eam.pm-notification-order-planning-fo",
        "sap.pattern.eam.pm-task-list-plan-fo",
        "sap.pattern.eam.pm-measuring-point-counter-fo",
        "sap.pattern.eam.pm-work-center-components-fo",
        "sap.pattern.eam.pm-confirmation-teco-settlement-fo",
    } <= fo_ids
    assert len(rule_ids) >= 6

    topics = {topic for item in items for topic in item["topics"]}
    assert {
        "maintenance-plan",
        "task-list",
        "measuring-point",
        "work-center",
        "settlement",
    } <= topics


def test_eam_pm_lifecycle_fo_patterns_have_review_questions_and_non_goals() -> None:
    for item in _items():
        if item["kind"] != "fo_pattern":
            continue
        assert item["required_questions"], item["id"]
        assert item["assumptions"], item["id"]
        assert item["non_goals"], item["id"]
        assert item["validation_notes"], item["id"]
        joined = " ".join(item["non_goals"] + item["validation_notes"]).lower()
        assert "tenant" in joined or "evidence" in joined


def test_eam_pm_lifecycle_decision_rules_fail_closed_on_tenant_specifics() -> None:
    for item in _items():
        if item["kind"] != "decision_rule":
            continue
        rules = " ".join(str(rule) for rule in item.get("rules", [])).lower()
        assert "tenant" in rules or "evidence" in rules, item["id"]
        assert "fail" in item["summary"].lower() or "do not" in item["summary"].lower(), item["id"]


def test_eam_pm_lifecycle_fo_patterns_are_selected_for_bundle_query() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo",
        topic=(
            "FO maintenance plan task list measuring point work center "
            "settlement tenant questions"
        ),
        limit=24,
    )
    ids = {item["id"] for item in bundle["items"]}

    assert bundle["status"] == "ready"
    assert "sap.pattern.eam.pm-task-list-plan-fo" in ids
    assert "sap.pattern.eam.pm-measuring-point-counter-fo" in ids
    assert "sap.pattern.eam.pm-confirmation-teco-settlement-fo" in ids
