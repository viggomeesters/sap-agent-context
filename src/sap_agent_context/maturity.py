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


def write_maturity_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_gap_report(items: list[KnowledgeItem], *, root: Path) -> dict[str, Any]:
    """Turn maturity gaps into concrete follow-up candidates per slice/domain."""

    maturity = build_maturity_report(items, root=root)
    entries = [*maturity["domains"], *maturity["domain_density_profiles"]]
    slices = [_gap_entry(entry) for entry in entries]
    gaps = [entry for entry in slices if entry["gaps"]]
    return {
        "status": "passed",
        "definition": (
            "Gap report by slice: every missing maturity dimension maps to a "
            "follow-up candidate; slices with no gaps include an explicit "
            "no-follow-up reason."
        ),
        "dimensions": DEEP_TEMPLATE_DIMENSIONS,
        "slices": slices,
        "gaps": gaps,
    }


def write_gap_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
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


def _gap_entry(entry: dict[str, Any]) -> dict[str, Any]:
    missing = list(entry.get("missing_dimensions") or [])
    gaps = [
        {
            "dimension": dimension,
            "follow_up_task": _follow_up_task(str(entry["id"]), str(dimension)),
            "acceptance": _gap_acceptance(str(dimension)),
            "answer_impact": _gap_answer_impact(str(dimension)),
            "priority": _gap_priority(str(entry["promotion"]), str(dimension)),
        }
        for dimension in missing
    ]
    gaps.sort(key=lambda gap: gap["priority"])
    return {
        "id": entry["id"],
        "promotion": entry["promotion"],
        "status": entry["status"],
        "maturity": entry["maturity"],
        "gaps": gaps,
        "no_follow_up_reason": (
            "No missing maturity dimensions under current bounded slice gates."
            if not gaps
            else ""
        ),
    }


def _follow_up_task(slice_id: str, dimension: str) -> str:
    labels = {
        "source_references": "Add source-backed reference records with access/freshness metadata",
        "domain_anchors": "Add SAP app/object anchor records and relations",
        "fo_patterns": "Add FO pattern records with questions, assumptions and validation notes",
        "decision_rules": "Add fail-closed decision rules for tenant-specific behavior",
        "test_patterns": "Add test-pattern records or FO-output fixture coverage",
        "runtime_or_eval_coverage": "Add runtime/semantic/FO evaluation fixtures for the slice",
    }
    return f"{labels.get(dimension, 'Fill missing dimension')} for `{slice_id}`."


def _gap_acceptance(dimension: str) -> str:
    labels = {
        "source_references": "At least one cited source id with access and freshness is present.",
        "domain_anchors": "Bundle can cite a concrete app/object anchor for the slice.",
        "fo_patterns": "A consumer can draft bounded FO questions from source-backed patterns.",
        "decision_rules": "Tenant-specific uncertainty fails closed instead of generic prose.",
        "test_patterns": "The slice has regression coverage for positive/negative scenarios.",
        "runtime_or_eval_coverage": "Runtime, semantic or FO fixture proves retrieval visibility.",
    }
    return labels.get(dimension, "Missing dimension is filled and covered by tests.")


def _gap_answer_impact(dimension: str) -> str:
    labels = {
        "source_references": "Answers cannot cite authoritative evidence or freshness boundaries.",
        "domain_anchors": "Answers stay generic because no concrete SAP app/object can be named.",
        "fo_patterns": "Answers lack FO-ready questions, assumptions and design structure.",
        "decision_rules": (
            "Answers may overclaim tenant-specific behavior instead of failing closed."
        ),
        "test_patterns": "Answers can regress without positive/negative scenario coverage.",
        "runtime_or_eval_coverage": "Answers may not retrieve the slice in local/runtime queries.",
    }
    return labels.get(dimension, "Answers lose bounded evidence for this gap.")


def _gap_priority(promotion: str, dimension: str) -> int:
    dimension_rank = {
        "source_references": 10,
        "domain_anchors": 20,
        "decision_rules": 30,
        "fo_patterns": 40,
        "runtime_or_eval_coverage": 50,
        "test_patterns": 60,
    }
    promotion_offset = 0 if promotion == "required" else 100
    return promotion_offset + dimension_rank.get(dimension, 90)
