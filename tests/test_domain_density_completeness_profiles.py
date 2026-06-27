from __future__ import annotations

from pathlib import Path

from sap_agent_context.completeness import audit_completeness
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_domain_density_profiles_distinguish_deep_from_starter() -> None:
    report = audit_completeness(load_items(ROOT), root=ROOT)

    assert report["status"] == "passed"
    profiles = {profile["id"]: profile for profile in report["domain_density_profiles"]}
    eam = profiles["eam_pm_lifecycle"]
    analytics = profiles["analytics_extensibility_candidate"]

    assert eam["promotion"] == "required"
    assert eam["status"] == "deep"
    assert eam["items"] >= 100
    assert eam["kind_counts"]["fo_pattern"] >= 9
    assert eam["kind_counts"]["decision_rule"] >= 18
    assert eam["kind_counts"]["test_pattern"] >= 11
    assert eam["eval_fixture_token_hits"] >= 8
    assert not eam["missing"]

    assert analytics["promotion"] == "report_only"
    assert analytics["status"] in {"starter", "deep"}


def test_report_only_domain_density_gap_is_later_not_failure() -> None:
    report = audit_completeness(load_items(ROOT), root=ROOT)
    density_findings = [
        finding
        for finding in report["findings"]
        if finding["area"].startswith("domain-density:")
    ]

    assert report["critical"] == 0
    assert report["important"] == 0
    assert any(
        finding["severity"] == "later"
        and finding["area"] == "domain-density:analytics_extensibility_candidate"
        for finding in density_findings
    )
