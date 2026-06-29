"""Maturity reporting for bounded SAP context slices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sap_agent_context.completeness import audit_completeness
from sap_agent_context.domain_density import build_domain_density_heatmap
from sap_agent_context.model import KnowledgeItem

DEEP_TEMPLATE_DIMENSIONS = [
    "source_references",
    "domain_anchors",
    "fo_patterns",
    "decision_rules",
    "test_patterns",
    "runtime_or_eval_coverage",
]


def build_maturity_report(items: list[KnowledgeItem], *, root: Path) -> dict[str, Any]:
    """Build a compact maturity report for domains and declared density profiles."""

    heatmap = build_domain_density_heatmap(items)
    completeness = audit_completeness(items, root=root)
    domains = [
        _domain_maturity(domain, data)
        for domain, data in sorted(heatmap["domains"].items())
        if domain != "unclassified"
    ]
    profiles = [
        _profile_maturity(profile)
        for profile in completeness.get("domain_density_profiles", [])
        if isinstance(profile, dict)
    ]
    needs_curation = [
        entry
        for entry in [*domains, *profiles]
        if entry["maturity"] in {"needs_curation", "thin"}
    ]
    return {
        "status": "passed",
        "definition": (
            "Maturity is a planning signal mapped to the deep-domain template. "
            "It distinguishes required, report_only and needs-curation slices; "
            "it is not exhaustive SAP product coverage."
        ),
        "items": len(items),
        "dimensions": DEEP_TEMPLATE_DIMENSIONS,
        "domains": domains,
        "domain_density_profiles": profiles,
        "needs_curation": needs_curation,
    }


def render_maturity_markdown(report: dict[str, Any]) -> str:
    """Render the maturity report as reviewer-friendly Markdown."""

    lines = [
        "# SAP Agent Context maturity report",
        "",
        "> Planning signal only: this is not exhaustive SAP product coverage.",
        "",
        f"Total items: `{report['items']}`",
        "",
        "## Domain maturity",
        "",
        "| Domain | Maturity | Score | Missing dimensions |",
        "|---|---|---:|---|",
    ]
    for domain in report["domains"]:
        lines.append(
            "| {id} | {maturity} | {score:.2f} | {missing} |".format(
                id=domain["id"],
                maturity=domain["maturity"],
                score=domain["score"],
                missing=", ".join(domain["missing_dimensions"]) or "none",
            )
        )

    lines.extend(
        [
            "",
            "## Declared density profiles",
            "",
            "| Profile | Promotion | Status | Maturity | Score | Missing dimensions |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for profile in report["domain_density_profiles"]:
        lines.append(
            "| {id} | {promotion} | {status} | {maturity} | {score:.2f} | {missing} |".format(
                id=profile["id"],
                promotion=profile["promotion"],
                status=profile["status"],
                maturity=profile["maturity"],
                score=profile["score"],
                missing=", ".join(profile["missing_dimensions"]) or "none",
            )
        )

    lines.extend(
        [
            "",
            "## Consumer boundary",
            "",
            "- `required` means the declared slice must stay deep for the current gates.",
            "- `report_only` is visibility, not product-ready coverage.",
            "- `needs_curation` means follow-up work is required before final-use claims.",
            (
                "- Green maturity never means all SAP products, releases, tenants "
                "or local variants are covered."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def write_maturity_report(report: dict[str, Any], output: Path, output_format: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        output.write_text(render_maturity_markdown(report), encoding="utf-8")
        return
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _domain_maturity(domain: str, data: dict[str, Any]) -> dict[str, Any]:
    dimensions = {
        "source_references": int(data.get("source_references") or 0) > 0,
        "domain_anchors": _has_anchor(data),
        "fo_patterns": int(data.get("fo_patterns") or 0) > 0,
        "decision_rules": int(data.get("decision_rules") or 0) > 0,
        "test_patterns": int(data.get("test_patterns") or 0) > 0,
        "runtime_or_eval_coverage": int(data.get("eval_items") or 0) > 0,
    }
    return _entry(domain, "observed", "observed", dimensions)


def _profile_maturity(profile: dict[str, Any]) -> dict[str, Any]:
    kind_counts = profile.get("kind_counts") if isinstance(profile.get("kind_counts"), dict) else {}
    dimensions = {
        "source_references": int(profile.get("source_refs") or 0) > 0,
        "domain_anchors": any(
            int(kind_counts.get(kind) or 0) > 0 for kind in ["sap_app", "sap_object"]
        ),
        "fo_patterns": int(kind_counts.get("fo_pattern") or 0) > 0,
        "decision_rules": int(kind_counts.get("decision_rule") or 0) > 0,
        "test_patterns": int(kind_counts.get("test_pattern") or 0) > 0,
        "runtime_or_eval_coverage": int(profile.get("eval_fixture_token_hits") or 0) > 0,
    }
    return _entry(
        str(profile.get("id") or "profile"),
        str(profile.get("promotion") or "report_only"),
        str(profile.get("status") or "unknown"),
        dimensions,
    )


def _entry(
    entry_id: str,
    promotion: str,
    status: str,
    dimensions: dict[str, bool],
) -> dict[str, Any]:
    missing = [name for name, present in dimensions.items() if not present]
    score = sum(1 for present in dimensions.values() if present) / len(dimensions)
    if status == "deep" and not missing:
        maturity = "deep"
    elif score >= 0.67:
        maturity = "partial"
    else:
        maturity = "thin"
    if missing and promotion == "required":
        maturity = "needs_curation"
    return {
        "id": entry_id,
        "promotion": promotion,
        "status": status,
        "maturity": maturity,
        "score": round(score, 3),
        "dimensions": dimensions,
        "missing_dimensions": missing,
    }


def _has_anchor(data: dict[str, Any]) -> bool:
    kind_counts = data.get("kind_counts") if isinstance(data.get("kind_counts"), dict) else {}
    return any(int(kind_counts.get(kind) or 0) > 0 for kind in ["sap_app", "sap_object"])
