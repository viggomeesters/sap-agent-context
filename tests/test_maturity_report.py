from __future__ import annotations

import json
from pathlib import Path

import pytest

from sap_agent_context.cli import main
from sap_agent_context.maturity import build_gap_report, build_maturity_report
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_maturity_report_maps_domains_to_deep_domain_dimensions() -> None:
    report = build_maturity_report(load_items(ROOT), root=ROOT)

    assert report["status"] == "passed"
    assert report["dimensions"] == [
        "source_references",
        "domain_anchors",
        "fo_patterns",
        "decision_rules",
        "test_patterns",
        "runtime_or_eval_coverage",
    ]
    profiles = {profile["id"]: profile for profile in report["domain_density_profiles"]}
    assert profiles["eam_pm_lifecycle"]["promotion"] == "required"
    assert profiles["eam_pm_lifecycle"]["maturity"] == "deep"
    assert profiles["analytics_extensibility_candidate"]["promotion"] == "report_only"
    assert "not exhaustive SAP product coverage" in report["definition"]


def test_maturity_report_cli_outputs_json_only(tmp_path: Path, capsys) -> None:
    json_path = tmp_path / "maturity.json"

    assert main(["--root", str(ROOT), "maturity-report", "--output", str(json_path)]) == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["domain_density_profiles"]
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["command"] == "maturity-report"
    assert summary["output"] == str(json_path)
    assert summary["status"] == "passed"
    assert "domain_density_profiles" not in summary
    assert "# SAP Agent Context maturity report" not in captured.out


def test_maturity_report_rejects_markdown_format(tmp_path: Path) -> None:
    markdown_path = tmp_path / "maturity.md"

    with pytest.raises(SystemExit):
        main(
            [
                "--root",
                str(ROOT),
                "maturity-report",
                "--format",
                "markdown",
                "--output",
                str(markdown_path),
            ]
        )
    assert not markdown_path.exists()


def test_gap_report_turns_missing_dimensions_into_follow_up_candidates() -> None:
    report = build_gap_report(load_items(ROOT), root=ROOT)

    assert report["status"] == "passed"
    assert report["slices"]
    migration = next(entry for entry in report["slices"] if entry["id"] == "migration")
    if migration["gaps"]:
        assert migration["gaps"][0]["priority"] < 200
        assert migration["gaps"][0]["answer_impact"].startswith("Answers")
        assert migration["gaps"][0]["follow_up_task"].startswith("Add")
    else:
        assert migration["no_follow_up_reason"]
    no_gap = next(entry for entry in report["slices"] if entry["id"] == "eam_pm_lifecycle")
    assert no_gap["gaps"] == []
    assert no_gap["no_follow_up_reason"]


def test_gap_report_cli_outputs_json_only(tmp_path: Path, capsys) -> None:
    output = tmp_path / "gap-report.json"

    exit_code = main(
        [
            "--root",
            str(ROOT),
            "gap-report",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert "slices" in payload
    assert "gaps" in payload
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["command"] == "gap-report"
    assert summary["output"] == str(output)
    assert summary["status"] == "passed"
    assert "slices" not in summary
    assert "# SAP Agent Context gap report by slice" not in captured.out


def test_gap_report_rejects_markdown_format(tmp_path: Path) -> None:
    markdown_path = tmp_path / "gap-report.md"

    with pytest.raises(SystemExit):
        main(
            [
                "--root",
                str(ROOT),
                "gap-report",
                "--format",
                "markdown",
                "--output",
                str(markdown_path),
            ]
        )
    assert not markdown_path.exists()
