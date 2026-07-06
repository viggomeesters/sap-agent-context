from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISION = ROOT / "docs" / "vision.json"
REPO_GO_VISION = ROOT / "docs" / "repo-go-vision.json"
CONSULTANT_ANSWER_VISION = ROOT / "docs" / "consultant-answer-vision.json"
ANSWER_PROFILE_SCHEMA_PLAN = ROOT / "docs" / "plans" / "answer-profile-schema-go-plan.json"
OLD_VISION = ROOT / "docs" / "vision.md"
README = ROOT / "README.md"


def _payload() -> dict:
    return json.loads(VISION.read_text(encoding="utf-8"))


def test_vision_contract_is_json_agent_first_artifact() -> None:
    payload = _payload()

    assert payload["artifact_kind"] == "repo_design_vision_contract"
    assert payload["repo"]["name"] == "sap-agent-context"
    assert payload["repo"]["product_surface"] == "agent_first"
    assert payload["repo"]["canonical_agent_records"] == "records/*.jsonl"
    assert "agents" in payload["repo"]["primary_users"]
    assert not OLD_VISION.exists()


def test_vision_contract_states_cloneable_agent_first_product_direction() -> None:
    payload = _payload()
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    required = [
        "SAP professionals clone sap-agent-context",
        "agent-first SAP context",
        "agent-first",
        "self-contained",
        "fast",
        "compact",
        "evidence-backed",
        "fail-closed",
        "source-labelled context bundles",
        "without leaning on generic model memory",
    ]
    for phrase in required:
        assert phrase in text


def test_vision_contract_keeps_json_first_and_public_safe_boundaries() -> None:
    payload = _payload()
    principle_ids = {item["id"] for item in payload["principles"]}

    assert {"agent-first", "json-first", "public-safe", "reliable-fail-closed"} <= principle_ids
    assert payload["repo"]["canonical_agent_records"] == "records/*.jsonl"
    json_rule = next(item for item in payload["principles"] if item["id"] == "json-first")
    assert (
        "Generated report evidence and machine-consumable examples are JSON-only"
        in json_rule["rule"]
    )
    assert "Markdown may remain as narrative operating context" in json_rule["rule"]
    public_safe = payload["public_safety"]
    assert {"tenant URLs", "screenshots", "credentials"} <= set(public_safe["forbidden"])
    assert "SAP documentation mirror" in payload["non_goals"]
    assert "human wiki as the primary product surface" in payload["non_goals"]


def test_vision_contract_has_actionable_design_scorecard_and_review_checklist() -> None:
    payload = _payload()

    scorecard_ids = {item["id"] for item in payload["acceptance_scorecard"]}
    expected = {
        "agent-first",
        "self-contained",
        "fast",
        "compact",
        "reliable",
        "json-first",
        "public-safe",
        "retrieval-proof",
        "gap-steerable",
        "no-false-certainty",
    }
    assert expected <= scorecard_ids

    checklist = payload["review_checklist"]
    assert (
        "Does this help SAP professionals clone the repo as a practical agent resource?"
        in checklist
    )
    assert "Is the product surface still agent-first rather than prose-first?" in checklist
    assert "Did the final claim state what was proven and what remains outside scope?" in checklist


def test_readme_links_to_json_vision_as_design_contract() -> None:
    text = README.read_text(encoding="utf-8")

    assert "docs/vision.json" in text
    assert "docs/repo-go-vision.json" in text
    assert "docs/plans/answer-profile-schema-go-plan.json" in text
    assert "docs/consultant-answer-vision.json" in text
    assert "docs/vision.md" not in text
    assert "cloneable, local-first SAP context runtime" in text


def test_repo_go_vision_is_agent_workflow_planning_context() -> None:
    payload = json.loads(REPO_GO_VISION.read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    assert payload["schema"] == "agent-workflow.vision.v1"
    assert payload["kind"] == "vision"
    assert payload["id"] == "sap-agent-context-repo"
    assert payload["project"] == "sap-agent-context"
    assert payload["source_design_contract"] == "docs/vision.json"
    assert len(payload["principles"]) >= 3
    assert len(payload["non_goals"]) >= 3
    assert len(payload["load_bearing_assumptions"]) >= 3
    for assumption in payload["load_bearing_assumptions"]:
        assert {"claim", "fails_if", "cheapest_test", "kill_or_pivot"} <= set(assumption)
    assert "not a SAP documentation mirror" in text
    assert "Do not create broad SAP-content expansion tasks" in payload["next_planning_boundary"]
    assert CONSULTANT_ANSWER_VISION.exists()


def test_answer_profile_schema_go_plan_is_bounded_to_one_slice() -> None:
    payload = json.loads(ANSWER_PROFILE_SCHEMA_PLAN.read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    assert payload["schema"] == "agent-workflow.plan.v1"
    assert payload["kind"] == "plan"
    assert payload["plan_type"] == "parent"
    assert payload["id"] == "sap-agent-context-answer-profile-schema"
    assert payload["status"] == "draft"
    assert payload["vision_ref"] == "docs/repo-go-vision.json"
    assert payload["layer_vision_ref"] == "docs/consultant-answer-vision.json"
    assert payload["task_sequence"] == ["APS-001", "APS-002", "APS-003", "APS-004"]
    assert payload["progress"] == {"total": 4, "open": 4, "active": 0, "blocked": 0, "done": 0}
    assert "Do not add broad SAP content" in payload["planning_boundary"]
    assert "answer-profile-schema" in payload["created_from"]
    assert "Adding a new SAP domain" in text
    assert "Adding an LLM/free-form answer generator" in text
    required_task_fields = {
        "id",
        "summary",
        "status",
        "scope",
        "requirements",
        "acceptance",
        "verification",
    }
    for task in payload["task_refs"]:
        assert required_task_fields <= set(task)
        assert task["status"] == "open"
