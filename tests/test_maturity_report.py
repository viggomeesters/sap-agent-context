from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.cli import main
from sap_agent_context.maturity import build_maturity_report, render_maturity_markdown
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


def test_maturity_report_markdown_shows_boundaries() -> None:
    markdown = render_maturity_markdown(build_maturity_report(load_items(ROOT), root=ROOT))

    assert "# SAP Agent Context maturity report" in markdown
    assert "| Profile | Promotion | Status | Maturity | Score | Missing dimensions |" in markdown
    assert "report_only" in markdown
    assert "needs_curation" in markdown
    assert "Green maturity never means all SAP products" in markdown


def test_maturity_report_cli_outputs_json_and_markdown(tmp_path: Path, capsys) -> None:
    json_path = tmp_path / "maturity.json"
    markdown_path = tmp_path / "maturity.md"

    assert main(["--root", str(ROOT), "maturity-report", "--output", str(json_path)]) == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["domain_density_profiles"]

    assert (
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
        == 0
    )
    assert "# SAP Agent Context maturity report" in markdown_path.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "# SAP Agent Context maturity report" in captured.out
