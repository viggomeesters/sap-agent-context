from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples" / "deep-domain-pack-template.yaml"
DOC = ROOT / "docs" / "deep-domain-pack-template.md"
DENSITY_DOC = ROOT / "docs" / "domain-density-gates.md"
README = ROOT / "README.md"


def _template() -> dict[str, Any]:
    payload = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_deep_domain_pack_template_names_required_dimensions() -> None:
    template = _template()
    required_sections = template["required_sections"]

    assert template["derived_from"]["exemplar_slice"] == "eam_pm_lifecycle"
    assert {
        "source_references",
        "domain_anchors",
        "fo_patterns",
        "decision_rules",
        "test_patterns",
        "eval_fixtures",
        "retrieval_fixtures",
        "semantic_fixtures",
        "domain_density_profile",
    }.issubset(required_sections)

    assert "required_questions" in required_sections["fo_patterns"]["required_fields"]
    assert "non_goals" in required_sections["fo_patterns"]["required_fields"]
    assert "validation_notes" in required_sections["fo_patterns"]["required_fields"]
    assert required_sections["decision_rules"]["required_rule_fields"] == [
        "if",
        "then",
        "outcome",
    ]
    assert "schema/fo-output-evaluation-fixtures.yaml" in required_sections[
        "eval_fixtures"
    ]["required_files"]
    assert "schema/runtime-retrieval-fixtures.yaml" in required_sections[
        "retrieval_fixtures"
    ]["required_files"]
    assert "schema/semantic-model-fixtures.yaml" in required_sections[
        "semantic_fixtures"
    ]["required_files"]


def test_template_sample_domain_is_non_eam_and_report_only() -> None:
    template = _template()
    profile = template["sample_domain_profile"]
    skeleton = template["sample_pack_skeleton"]

    assert profile["id"] == "sample_reporting_slice"
    assert profile["promotion"] == "report_only"
    assert "eam" not in profile["topic_tokens"]
    assert profile["required_kind_counts"]["fo_pattern"] >= 2
    assert profile["required_kind_counts"]["decision_rule"] >= 3

    item_kinds = {item["kind"] for item in skeleton["items"]}
    assert {"external_reference", "sap_object", "fo_pattern", "decision_rule"}.issubset(
        item_kinds
    )
    fo_item = next(item for item in skeleton["items"] if item["kind"] == "fo_pattern")
    assert fo_item["required_questions"]
    assert fo_item["assumptions"]
    assert fo_item["non_goals"]
    assert fo_item["validation_notes"]


def test_template_public_safety_caveat_blocks_exhaustive_sap_claims() -> None:
    template = _template()
    public_safety = template["public_safety"]
    combined = yaml.safe_dump(public_safety).lower()

    assert "bounded implementation-pack coverage" in combined
    assert "not exhaustive sap product coverage" in combined
    assert "customer/client names" in public_safety["forbidden_content"]
    assert "copied proprietary SAP documentation" in public_safety["forbidden_content"]
    assert ".env files" in combined


def test_template_is_documented_and_linked_from_density_docs_and_readme() -> None:
    doc = DOC.read_text(encoding="utf-8")
    density_doc = DENSITY_DOC.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    density_doc_flat = " ".join(density_doc.split())

    assert "examples/deep-domain-pack-template.yaml" in doc
    assert "not exhaustive SAP product coverage" in doc
    assert "promotion: report_only" in doc
    assert "promotion: required" in doc
    assert "later" in doc
    assert "important" in doc

    assert "Deep domain pack template" in density_doc
    assert "bounded implementation-pack coverage" in density_doc_flat
    assert "Deep domain pack template" in readme
