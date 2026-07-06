from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "schema" / "answer-profiles.json"
PROFILE_SCHEMA = ROOT / "schema" / "answer-profiles.schema.json"
ANSWER_SCENARIOS = ROOT / "schema" / "answer-scenario-fixtures.yaml"


REQUIRED_PROFILE_FIELDS = {
    "id",
    "classification",
    "status",
    "support_ids",
    "positive_fixture_ids",
    "adversarial_fixture_ids",
    "required_answer_citation_ids",
    "curation_reason_required",
}

READY_CLASSIFICATIONS = {
    "analytics_extensibility",
    "integration_security",
    "material_fields",
    "mtart",
    "org_model",
    "p2p",
    "procurement_workflow",
}


def _payload() -> dict[str, Any]:
    return json.loads(PROFILES.read_text(encoding="utf-8"))


def _fixture_ids() -> set[str]:
    payload = yaml.safe_load(ANSWER_SCENARIOS.read_text(encoding="utf-8")) or {}
    return {str(fixture["id"]) for fixture in payload.get("fixtures", [])}


def test_answer_profiles_contract_is_json_agent_artifact() -> None:
    payload = _payload()
    schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))

    assert schema["$id"].endswith("answer-profiles.schema.json")
    assert payload["schema"] == "sap-agent-context.answer-profiles.v1"
    assert payload["artifact_kind"] == "answer_profiles"
    assert "not SAP truth" in payload["purpose"]
    assert "tenant proof" in payload["purpose"]


def test_answer_profiles_have_unique_ids_and_required_shape() -> None:
    payload = _payload()
    profiles = payload["profiles"]
    ids = [profile["id"] for profile in profiles]
    classifications = [profile["classification"] for profile in profiles]

    assert len(ids) == len(set(ids))
    assert len(classifications) == len(set(classifications))
    for profile in profiles:
        assert set(profile) >= REQUIRED_PROFILE_FIELDS
        assert profile["status"] in {"ready", "needs_curation"}
        assert isinstance(profile["curation_reason_required"], bool)
        for key in (
            "support_ids",
            "positive_fixture_ids",
            "adversarial_fixture_ids",
            "required_answer_citation_ids",
            "boundary_notes",
        ):
            assert len(profile.get(key, [])) == len(set(profile.get(key, [])))


def test_ready_answer_profiles_name_support_and_positive_fixtures() -> None:
    fixture_ids = _fixture_ids()
    profiles = {profile["classification"]: profile for profile in _payload()["profiles"]}

    assert set(profiles) >= READY_CLASSIFICATIONS
    for classification in READY_CLASSIFICATIONS:
        profile = profiles[classification]
        assert profile["status"] == "ready"
        assert profile["support_ids"], classification
        assert profile["positive_fixture_ids"], classification
        assert set(profile["positive_fixture_ids"]) <= fixture_ids
        assert set(profile["required_answer_citation_ids"]) <= set(profile["support_ids"])
        assert profile["curation_reason_required"] is False


def test_fail_closed_profiles_are_explicit_and_not_ready() -> None:
    profiles = {profile["classification"]: profile for profile in _payload()["profiles"]}

    for classification in {"generic", "modules", "unsupported_configuration"}:
        profile = profiles[classification]
        assert profile["status"] == "needs_curation"
        assert profile["curation_reason_required"] is True
        assert profile["required_answer_citation_ids"] == []
        assert profile["boundary_notes"]

    assert profiles["modules"]["adversarial_fixture_ids"] == ["vague_sap_modules"]
    assert profiles["generic"].get("adversarial_probe_ids") == [
        "generic_api_report_needs_curation",
        "generic_release_strategy_needs_curation",
    ]


def test_answer_profiles_preserve_current_no_broad_expansion_boundary() -> None:
    text = json.dumps(_payload(), ensure_ascii=False, sort_keys=True)

    assert "sap help mirror" not in text.lower()
    assert "customer-specific mappings" not in text.lower()
    assert "Adding a new SAP domain" not in text
    assert "not SAP truth" in text
    assert "target-system evidence" in text
    assert "generic_api_report_needs_curation" in text
    assert "generic_release_strategy_needs_curation" in text
