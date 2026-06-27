"""Domain-density coverage heatmap for SAP Agent Context."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from sap_agent_context.model import KnowledgeItem

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "eam_pm": (
        "eam",
        "plant-maintenance",
        "pm",
        "equipment",
        "functional-location",
        "maintenance",
        "technical-object",
        "ie01",
        "ie02",
        "ie03",
        "ih08",
    ),
    "material_master": ("material", "material-master", "mrp", "valuation", "batch", "serial"),
    "procurement": (
        "procurement",
        "purchase",
        "purchasing",
        "supplier",
        "purchase-order",
        "invoice",
    ),
    "sales_otc": ("sales", "delivery", "billing", "output", "order-to-cash"),
    "integration": ("integration", "api", "odata", "event", "payload", "cpi", "idoc"),
    "migration": ("migration", "migration-cockpit", "load-template", "field-mapping"),
    "finance": ("finance", "fi", "ap", "invoice", "accounting", "valuation"),
    "security_authorizations": ("authorization", "role", "access", "catalog", "business-role"),
    "analytics_extensibility": ("analytics", "extensibility", "custom-field", "embedded-analytics"),
}

EAM_PM_LIFECYCLE_SLICES: dict[str, tuple[str, ...]] = {
    "equipment": ("equipment", "ie01", "ie02", "ie03", "ih08"),
    "functional-location": ("functional-location", "functional location"),
    "notification": ("notification", "maintenance-notification"),
    "maintenance-order": ("maintenance-order", "maintenance order"),
    "maintenance-plan": ("maintenance-plan", "maintenance plan", "maintenance-item"),
    "task-list": ("task-list", "task list"),
    "measuring-point-counter": (
        "measuring-point",
        "measuring point",
        "counter",
        "measurement-document",
    ),
    "work-center": ("work-center", "work center"),
    "bom-spares": ("bom", "spares", "spare", "component"),
    "confirmation": ("confirmation", "confirm"),
    "technical-completion": ("technical-completion", "teco", "technical completion"),
    "settlement": ("settlement", "settle"),
    "permits-safety": ("permit", "safety", "work permit", "lockout"),
}

EVAL_HINTS = ("fixture", "evaluation", "test-pattern", "runtime-retrieval", "semantic")


def build_domain_density_heatmap(items: Iterable[KnowledgeItem]) -> dict[str, Any]:
    """Build a deterministic domain-density heatmap from loaded knowledge items."""

    item_list = list(items)
    domain_kind_counts: dict[str, Counter[str]] = defaultdict(Counter)
    domain_source_kinds: dict[str, Counter[str]] = defaultdict(Counter)
    domain_source_specificity: dict[str, Counter[str]] = defaultdict(Counter)
    domain_eval_items: dict[str, list[str]] = defaultdict(list)
    domain_totals: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter(item.kind for item in item_list)
    access_counts: Counter[str] = Counter(item.access for item in item_list)
    source_kind_counts: Counter[str] = Counter()
    source_specificity_counts: Counter[str] = Counter()

    for item in item_list:
        source = _mapping(item.data.get("source"))
        source_kind = str(source.get("kind") or "missing")
        source_specificity = str(source.get("specificity") or "missing")
        source_kind_counts[source_kind] += 1
        source_specificity_counts[source_specificity] += 1
        item_domains = classify_domains(item)
        if not item_domains:
            item_domains = ["unclassified"]
        for domain in item_domains:
            domain_totals[domain] += 1
            domain_kind_counts[domain][item.kind] += 1
            domain_source_kinds[domain][source_kind] += 1
            domain_source_specificity[domain][source_specificity] += 1
            if item.kind == "test_pattern" or _contains_any(item, EVAL_HINTS):
                domain_eval_items[domain].append(item.item_id)

    eam_slices = {
        name: _slice_report(item_list, keywords)
        for name, keywords in EAM_PM_LIFECYCLE_SLICES.items()
    }

    weak_domains = _weak_domain_reports(domain_totals, domain_kind_counts, domain_eval_items)

    return {
        "status": "passed",
        "definition": (
            "Domain-density heatmap for planning: shows coverage shape and weak areas; "
            "it is not an exhaustive SAP product coverage claim."
        ),
        "items": len(item_list),
        "kind_counts": dict(sorted(kind_counts.items())),
        "access_counts": dict(sorted(access_counts.items())),
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "source_specificity_counts": dict(sorted(source_specificity_counts.items())),
        "domains": {
            domain: {
                "items": domain_totals[domain],
                "kind_counts": dict(sorted(domain_kind_counts[domain].items())),
                "source_kind_counts": dict(sorted(domain_source_kinds[domain].items())),
                "source_specificity_counts": dict(
                    sorted(domain_source_specificity[domain].items())
                ),
                "fo_patterns": domain_kind_counts[domain]["fo_pattern"],
                "test_patterns": domain_kind_counts[domain]["test_pattern"],
                "decision_rules": domain_kind_counts[domain]["decision_rule"],
                "source_references": domain_kind_counts[domain]["external_reference"],
                "eval_items": len(set(domain_eval_items[domain])),
            }
            for domain in sorted(domain_totals)
        },
        "eam_pm_lifecycle": eam_slices,
        "weak_domains": weak_domains,
    }


def render_heatmap_markdown(report: dict[str, Any]) -> str:
    """Render a compact Markdown report for docs and review."""

    lines = [
        "# SAP Agent Context coverage heatmap",
        "",
        (
            "> Generated from current knowledge items. This is a planning heatmap, "
            "not an exhaustive SAP product coverage claim."
        ),
        "",
        f"Total items: `{report['items']}`",
        "",
        "## Domain density",
        "",
        "| Domain | Items | Sources | FO patterns | Decision rules | Test patterns | Eval items |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for domain, data in report["domains"].items():
        lines.append(
            "| {domain} | {items} | {sources} | {fo} | {rules} | {tests} | {evals} |".format(
                domain=domain,
                items=data["items"],
                sources=data["source_references"],
                fo=data["fo_patterns"],
                rules=data["decision_rules"],
                tests=data["test_patterns"],
                evals=data["eval_items"],
            )
        )

    lines.extend(
        [
            "",
            "## EAM/PM lifecycle slices",
            "",
            "| Slice | Items | FO patterns | Decision rules | Test patterns | Status |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for slice_name, data in report["eam_pm_lifecycle"].items():
        lines.append(
            "| {slice} | {items} | {fo} | {rules} | {tests} | {status} |".format(
                slice=slice_name,
                items=data["items"],
                fo=data["kind_counts"].get("fo_pattern", 0),
                rules=data["kind_counts"].get("decision_rule", 0),
                tests=data["kind_counts"].get("test_pattern", 0),
                status=data["status"],
            )
        )

    lines.extend(["", "## Weak domains", ""])
    if report["weak_domains"]:
        for finding in report["weak_domains"]:
            lines.append(f"- **{finding['domain']}**: {finding['message']}")
    else:
        lines.append("- No weak domains under the current planning heuristic.")

    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- `records/*.jsonl` remains the canonical agent record surface.",
            "- YAML is legacy authoring/import format only.",
            (
                "- This heatmap should guide filling; it must not become a fake "
                "exhaustive SAP completeness claim."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def write_heatmap(report: dict[str, Any], output: Path, output_format: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        output.write_text(render_heatmap_markdown(report), encoding="utf-8")
        return
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def classify_domains(item: KnowledgeItem) -> list[str]:
    haystack = _item_haystack(item)
    return [
        domain
        for domain, keywords in DOMAIN_KEYWORDS.items()
        if _text_has_any(haystack, keywords)
    ]


def _weak_domain_reports(
    domain_totals: Counter[str],
    domain_kind_counts: dict[str, Counter[str]],
    domain_eval_items: dict[str, list[str]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for domain in sorted(domain_totals):
        if domain == "unclassified":
            continue
        counts = domain_kind_counts[domain]
        missing = []
        if counts["external_reference"] == 0:
            missing.append("source references")
        if counts["fo_pattern"] == 0:
            missing.append("FO patterns")
        if counts["decision_rule"] == 0:
            missing.append("decision rules")
        if counts["test_pattern"] == 0 and not domain_eval_items[domain]:
            missing.append("test/eval coverage")
        if missing:
            findings.append(
                {
                    "domain": domain,
                    "message": "Missing or thin " + ", ".join(missing) + ".",
                }
            )
    return findings


def _slice_report(items: list[KnowledgeItem], keywords: tuple[str, ...]) -> dict[str, Any]:
    matched = [item for item in items if _contains_any(item, keywords)]
    kind_counts = Counter(item.kind for item in matched)
    if not matched:
        status = "missing"
    elif kind_counts["fo_pattern"] and kind_counts["decision_rule"] and kind_counts["test_pattern"]:
        status = "dense"
    elif kind_counts["fo_pattern"] or kind_counts["decision_rule"] or kind_counts["test_pattern"]:
        status = "thin"
    else:
        status = "anchor-only"
    return {
        "items": len(matched),
        "status": status,
        "kind_counts": dict(sorted(kind_counts.items())),
        "sample_ids": [item.item_id for item in matched[:8]],
    }


def _contains_any(item: KnowledgeItem, keywords: Iterable[str]) -> bool:
    return _text_has_any(_item_haystack(item), keywords)


def _text_has_any(text: str, keywords: Iterable[str]) -> bool:
    return any(_has_keyword(text, keyword.lower()) for keyword in keywords)


def _has_keyword(text: str, keyword: str) -> bool:
    """Return true when keyword appears as a token/phrase, not inside another word.

    Short SAP abbreviations such as ``fi`` and ``ap`` are useful domain signals,
    but substring matching would classify nearly every item via words like
    ``specificity`` or ``sap``. Use alphanumeric boundaries while still allowing
    hyphenated SAP terms such as ``functional-location``.
    """

    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def _item_haystack(item: KnowledgeItem) -> str:
    pieces = [
        item.item_id,
        item.title,
        item.kind,
        item.summary,
        " ".join(item.topics),
        " ".join(item.used_for),
    ]
    source = _mapping(item.data.get("source"))
    pieces.extend(str(source.get(key) or "") for key in ("kind", "title", "specificity"))
    for claim in item.data.get("claims") or []:
        if isinstance(claim, dict):
            pieces.append(str(claim.get("statement") or ""))
            pieces.extend(str(evidence) for evidence in claim.get("evidence") or [])
    return " ".join(piece for piece in pieces if piece).lower()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
