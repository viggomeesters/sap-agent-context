from __future__ import annotations

import json
from pathlib import Path

import pytest

from sap_agent_context.cli import main
from sap_agent_context.content_curation import build_content_curation_report
from sap_agent_context.model import KnowledgeItem
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_content_curation_report_samples_claims_without_certifying_everything() -> None:
    report = build_content_curation_report(load_items(ROOT), sample_size=2)

    assert report["status"] in {"passed", "needs_curation"}
    assert report["scope"]["mode"] == "sampling"
    assert "not exhaustive claim-by-claim SAP content certification" in report["scope"]["boundary"]
    assert report["summary"]["sampled_claims"] > 0
    assert report["summary"]["sampled_claims"] <= report["summary"]["total_claims"]
    assert report["summary"]["sampled_packs"] >= 3
    assert report["samples"] == build_content_curation_report(
        load_items(ROOT), sample_size=2
    )["samples"]

    sample = report["samples"][0]
    assert {
        "claim_id",
        "item_id",
        "pack_path",
        "statement",
        "confidence",
        "checks",
        "maturity",
        "review_decision",
    } <= set(sample)
    assert set(sample["checks"]) == {
        "source_access_boundary",
        "freshness_present",
        "evidence_present",
        "claim_scope_boundary",
    }
    assert sample["maturity"]["level"] in {"L0", "L1", "L2", "L3"}
    assert "next_step" in sample["maturity"]
    index_row = report["claim_maturity_index"][0]
    assert "sampled" in index_row
    assert "review_decision" not in index_row
    assert set(report["summary"]["maturity_distribution"]) == {"L0", "L1", "L2", "L3"}
    assert len(report["claim_maturity_index"]) == report["summary"]["total_claims"]


def test_content_curation_report_checks_fail_closed_boundaries() -> None:
    report = build_content_curation_report(load_items(ROOT), sample_size=4)

    tenant_sensitive = [
        sample
        for sample in report["samples"]
        if any(
            token in sample["statement"].lower()
            for token in ["tenant", "client", "customizing", "configured"]
        )
    ]
    assert tenant_sensitive, "expected at least one sampled tenant/customizing-sensitive claim"
    assert all(
        sample["checks"]["claim_scope_boundary"]["status"] == "passed"
        for sample in tenant_sensitive
    )
    assert all(
        sample["review_decision"] in {"sample_passed", "curation_needed"}
        for sample in report["samples"]
    )


def test_current_claims_have_no_l0_boundary_failures_after_targeted_fixes() -> None:
    report = build_content_curation_report(load_items(ROOT), sample_size=3)

    assert report["summary"]["curation_needed"] == 0
    assert report["summary"]["sampled_maturity_distribution"]["L0"] == 0
    assert report["summary"]["maturity_distribution"] == {"L0": 0, "L1": 773, "L2": 0, "L3": 0}
    assert report["status"] == "passed"
    assert report["summary"]["lowest_maturity"] == "L1"


def test_content_curation_report_cli_outputs_json_only(tmp_path: Path, capsys) -> None:
    json_path = tmp_path / "curation.json"

    assert (
        main(
            [
                "--root",
                str(ROOT),
                "curation-report",
                "--sample-size",
                "2",
                "--output",
                str(json_path),
            ]
        )
        == 0
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["scope"]["mode"] == "sampling"
    assert payload["summary"]["sample_size_per_pack"] == 2
    assert "not exhaustive claim-by-claim SAP content certification" in payload[
        "scope"
    ]["boundary"]
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["command"] == "curation-report"
    assert summary["output"] == str(json_path)
    assert summary["status"] in {"passed", "needs_curation"}
    assert summary["curation_needed"] >= 0
    assert summary["maturity_distribution"] == payload["summary"]["maturity_distribution"]
    assert summary["maturity_blocked_claims"] == payload["summary"]["maturity_distribution"]["L0"]
    assert summary["lowest_maturity"] in {"L0", "L1", "L2", "L3"}
    assert "samples" not in captured.out
    assert "claim_maturity_index" not in captured.out


def test_missing_explicit_confidence_stays_l1_not_agent_ready() -> None:
    item = _item_with_claim(
        claim={
            "statement": "Display equipment master data from the referenced internal pattern.",
            "evidence": ["sap.ref.synthetic-source"],
        }
    )

    report = build_content_curation_report([item], sample_size=1)

    assert report["status"] == "passed"
    index_row = report["claim_maturity_index"][0]
    assert index_row["level"] == "L1"
    assert index_row["status"] == "metadata_ready"
    assert index_row["reasons"] == ["explicit_confidence_medium_or_high"]
    assert report["samples"][0]["confidence"] is None
    assert report["samples"][0]["confidence_present"] is False


def test_explicit_medium_confidence_can_reach_l2_not_l3() -> None:
    item = _item_with_claim(
        claim={
            "statement": "Display equipment master data from the referenced internal pattern.",
            "confidence": "medium",
            "evidence": ["sap.ref.synthetic-source"],
        }
    )

    report = build_content_curation_report([item], sample_size=1)

    assert report["status"] == "passed"
    index_row = report["claim_maturity_index"][0]
    assert index_row["level"] == "L2"
    assert index_row["status"] == "agent_ready"
    assert "confidence_high" in index_row["reasons"]


def test_claim_maturity_promotes_only_explicit_expert_review_to_l3() -> None:
    item = _item_with_claim(
        claim={
            "statement": "Display equipment master data from the referenced public catalog entry.",
            "confidence": "high",
            "evidence": ["sap.ref.expert-reviewed-public-page"],
            "usage_constraints": ["Expert reviewed and curated for public generic agent use."],
            "curation": {
                "expert_review": {
                    "status": "reviewed",
                    "reviewer_role": "sap_domain_expert",
                    "reviewed_at": "2026-07-02",
                    "evidence_id": "sap.ref.expert-reviewed-public-page",
                }
            },
        },
        access="public",
        source={
            "kind": "public_url",
            "title": "SAP public reference",
            "url": "https://example.com/sap-public-reference",
            "specificity": "exact_page",
        },
    )

    report = build_content_curation_report([item], sample_size=1)

    assert report["status"] == "passed"
    assert report["summary"]["maturity_distribution"] == {"L0": 0, "L1": 0, "L2": 0, "L3": 1}
    assert report["claim_maturity_index"][0]["level"] == "L3"


def test_claim_maturity_blocks_missing_evidence_before_l1() -> None:
    item = _item_with_claim(
        claim={
            "statement": "Equipment status behavior should be verified in the target tenant.",
            "confidence": "medium",
            "evidence": [],
        }
    )

    report = build_content_curation_report([item], sample_size=1)

    assert report["status"] == "needs_curation"
    assert report["summary"]["maturity_distribution"]["L0"] == 1
    assert report["claim_maturity_index"][0]["status"] == "blocked"
    assert report["claim_maturity_index"][0]["reasons"] == ["evidence_present"]


def _item_with_claim(
    *,
    claim: dict[str, object],
    access: str = "internal_derived",
    source: dict[str, object] | None = None,
) -> KnowledgeItem:
    return KnowledgeItem(
        path=ROOT / "knowledge" / "synthetic-pack.yaml",
        data={
            "id": "sap.synthetic.claim-maturity",
            "title": "Synthetic claim maturity fixture",
            "kind": "sap_object",
            "access": access,
            "source": source
            or {
                "kind": "internal_pattern",
                "title": "Synthetic source",
                "specificity": "internal_pattern",
            },
            "freshness": {
                "valid_from": "2026-01-01",
                "retrieved_at": "2026-01-01",
                "review_after": "2026-07-01",
                "expires_at": "2027-01-01",
            },
            "usage_constraints": [
                "Verify this internal-derived context in the target SAP tenant/system before use."
            ],
            "claims": [claim],
        },
    )


def test_content_curation_report_rejects_markdown_format(tmp_path: Path) -> None:
    markdown_path = tmp_path / "curation.md"

    with pytest.raises(SystemExit):
        main(
            [
                "--root",
                str(ROOT),
                "curation-report",
                "--sample-size",
                "1",
                "--format",
                "markdown",
                "--output",
                str(markdown_path),
            ]
        )
    assert not markdown_path.exists()
