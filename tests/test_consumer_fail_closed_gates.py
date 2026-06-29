from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "schema" / "consumer-fail-closed-fixtures.yaml"
DOC = ROOT / "docs" / "context-bundle-consumer-contract.md"


def _load_fixtures() -> list[dict[str, Any]]:
    payload = yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))
    assert payload["schema"] == "sap-agent-context.consumer-fail-closed-fixtures.v1"
    return payload["fixtures"]


def _evaluate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    bundle = fixture.get("bundle") or {}
    profile = fixture.get("profile") or {}
    output = fixture.get("consumer_output") or {}
    text = str(output.get("text") or "").lower()

    if output.get("status") == "final" and bundle.get("status") == "needs_curation":
        reasons.append("needs_curation_misuse")
    if output.get("status") == "final" and bundle.get("gaps") and "gap" not in text:
        reasons.append("gaps_hidden")
    if output.get("status") == "final" and not bundle.get("citations") and profile == {}:
        reasons.append("missing_source")
    raw_quality = bundle.get("quality_signals")
    quality = raw_quality if isinstance(raw_quality, dict) else {}
    if (
        output.get("status") == "final"
        and int(quality.get("source_url_count") or 0) == 0
        and ("threshold" in text or "z_" in text or "customer-ready" in text)
    ):
        reasons.append("missing_tenant_evidence")
    if "€10,000".lower() in text or "z_ap_manager" in text:
        reasons.append("invented_role_or_threshold")
    if profile.get("promotion") == "report_only" and (
        "customer-ready" in text or "complete" in text
    ):
        reasons.append("report_only_misuse")

    return {"fail_closed": bool(reasons), "reasons": sorted(set(reasons))}


def test_consumer_fail_closed_fixtures_match_expected_verdicts() -> None:
    fixtures = _load_fixtures()

    assert len(fixtures) >= 5
    for fixture in fixtures:
        actual = _evaluate_fixture(fixture)
        expected = fixture["expected"]
        assert actual["fail_closed"] is expected["fail_closed"], fixture["id"]
        for reason in expected["reasons"]:
            assert reason in actual["reasons"], fixture["id"]


def test_consumer_fail_closed_fixtures_cover_required_risks() -> None:
    fixtures = _load_fixtures()
    all_reasons = {reason for fixture in fixtures for reason in fixture["expected"]["reasons"]}

    assert "missing_source" in all_reasons
    assert "missing_tenant_evidence" in all_reasons
    assert "report_only_misuse" in all_reasons
    assert "needs_curation_misuse" in all_reasons
    assert "gaps_hidden" in all_reasons


def test_context_bundle_contract_points_to_fail_closed_gate_fixtures() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "schema/consumer-fail-closed-fixtures.yaml" in text
    assert "missing source" in text
    assert "report_only misuse" in text
