from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.cli import main
from sap_agent_context.content_curation import (
    build_content_curation_report,
    render_content_curation_markdown,
)
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


def test_content_curation_markdown_names_residual_risk_boundary() -> None:
    markdown = render_content_curation_markdown(
        build_content_curation_report(load_items(ROOT), sample_size=1)
    )

    assert "# SAP Agent Context content curation sample" in markdown
    assert "repo-level gates" in markdown
    assert "not exhaustive claim-by-claim SAP content certification" in markdown
    assert "| Claim | Item | Decision | Checks |" in markdown


def test_content_curation_report_cli_outputs_json_and_markdown(tmp_path: Path, capsys) -> None:
    json_path = tmp_path / "curation.json"
    markdown_path = tmp_path / "curation.md"

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

    assert (
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
        == 0
    )
    assert "# SAP Agent Context content curation sample" in markdown_path.read_text(
        encoding="utf-8"
    )
    captured = capsys.readouterr()
    assert "SAP Agent Context content curation sample" in captured.out
