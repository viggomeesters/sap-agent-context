from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISION = ROOT / "docs" / "vision.md"
README = ROOT / "README.md"


def test_vision_doc_states_cloneable_agent_first_product_direction() -> None:
    text = VISION.read_text(encoding="utf-8")

    required = [
        "SAP professionals clone `sap-agent-context`",
        "agent-first SAP context",
        "agent-only product surface",
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


def test_vision_doc_keeps_json_first_and_public_safe_boundaries() -> None:
    text = VISION.read_text(encoding="utf-8")

    required = [
        "`records/*.jsonl` is the canonical agent record surface",
        "Generated report evidence and machine-consumable examples are JSON-only",
        "Markdown may remain as narrative operating context for maintainers and agents",
        "Never store customer names, tenant URLs, screenshots, SAP exports",
        "not a SAP documentation mirror",
        "not a human wiki as the primary product surface",
    ]
    for phrase in required:
        assert phrase in text


def test_vision_doc_has_actionable_design_scorecard_and_review_checklist() -> None:
    text = VISION.read_text(encoding="utf-8")

    scorecard_checks = [
        "Agent-only",
        "Self-contained",
        "Fast",
        "Compact",
        "Reliable",
        "JSON-first",
        "Public-safe",
        "Retrieval-proof",
        "Gap-steerable",
        "No false certainty",
    ]
    for phrase in scorecard_checks:
        assert phrase in text

    checklist_phrases = [
        "Does this help SAP professionals clone the repo as a practical agent resource?",
        "Is the product surface still agent-first rather than prose-first?",
        "Did the final claim state what was proven and what remains outside scope?",
    ]
    for phrase in checklist_phrases:
        assert phrase in text


def test_readme_links_to_vision_as_design_contract() -> None:
    text = README.read_text(encoding="utf-8")

    assert "docs/vision.md" in text
    assert "cloneable, local-first SAP context runtime" in text
