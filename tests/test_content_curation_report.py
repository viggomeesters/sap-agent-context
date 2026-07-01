from __future__ import annotations

import json
from pathlib import Path

import pytest

from sap_agent_context.cli import main
from sap_agent_context.content_curation import build_content_curation_report
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
        "checks",
        "review_decision",
    } <= set(sample)
    assert set(sample["checks"]) == {
        "source_access_boundary",
        "freshness_present",
        "evidence_present",
        "claim_scope_boundary",
    }


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


def test_current_sampled_claims_do_not_need_curation_after_targeted_fixes() -> None:
    report = build_content_curation_report(load_items(ROOT), sample_size=3)

    assert report["summary"]["curation_needed"] == 0
    assert report["status"] == "passed"


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
    assert "samples" not in captured.out


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
