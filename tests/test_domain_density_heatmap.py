from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.domain_density import (
    EAM_PM_LIFECYCLE_SLICES,
    build_domain_density_heatmap,
    render_heatmap_markdown,
)
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def test_domain_density_heatmap_reports_domain_shape_and_eam_lifecycle_gaps() -> None:
    report = build_domain_density_heatmap(load_items(ROOT))

    assert report["status"] == "passed"
    assert report["items"] >= 637
    assert report["domains"]["eam_pm"]["items"] >= 1
    assert report["domains"]["eam_pm"]["fo_patterns"] >= 1
    assert report["domains"]["eam_pm"]["test_patterns"] >= 1
    assert set(EAM_PM_LIFECYCLE_SLICES).issubset(report["eam_pm_lifecycle"])

    for name in [
        "maintenance-plan",
        "task-list",
        "measuring-point-counter",
        "work-center",
        "settlement",
        "permits-safety",
    ]:
        assert name in report["eam_pm_lifecycle"]
        assert report["eam_pm_lifecycle"][name]["status"] in {
            "missing",
            "anchor-only",
            "thin",
            "dense",
        }


def test_domain_density_heatmap_exposes_source_and_eval_coverage() -> None:
    report = build_domain_density_heatmap(load_items(ROOT))
    eam = report["domains"]["eam_pm"]

    assert "source_kind_counts" in eam
    assert "source_specificity_counts" in eam
    assert "eval_items" in eam
    assert report["source_kind_counts"]
    assert report["source_specificity_counts"]
    assert isinstance(report["weak_domains"], list)


def test_domain_density_heatmap_markdown_is_reviewable() -> None:
    report = build_domain_density_heatmap(load_items(ROOT))
    markdown = render_heatmap_markdown(report)

    assert "# SAP Agent Context coverage heatmap" in markdown
    assert "## Domain density" in markdown
    assert "## EAM/PM lifecycle slices" in markdown
    assert "maintenance-plan" in markdown
    assert "records/*.jsonl" in markdown


def test_domain_density_heatmap_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    from sap_agent_context.cli import main

    json_output = tmp_path / "heatmap.json"
    markdown_output = tmp_path / "heatmap.md"

    assert main(["--root", str(ROOT), "domain-density-heatmap", "--output", str(json_output)]) == 0
    assert (
        main(
            [
                "--root",
                str(ROOT),
                "domain-density-heatmap",
                "--format",
                "markdown",
                "--output",
                str(markdown_output),
            ]
        )
        == 0
    )

    payload = json.loads(json_output.read_text())
    assert payload["status"] == "passed"
    assert "eam_pm_lifecycle" in payload
    assert markdown_output.read_text().startswith("# SAP Agent Context coverage heatmap")
