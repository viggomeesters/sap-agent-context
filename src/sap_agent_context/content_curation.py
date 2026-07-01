"""Content curation sampling reports for SAP Agent Context.

This module deliberately samples claims. It does not certify every SAP claim in
all domain packs; it makes the residual risk boundary executable and reviewable.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sap_agent_context.model import KnowledgeItem

TENANT_SENSITIVE_TERMS = {
    "tenant",
    "client",
    "customizing",
    "configured",
    "configuration",
    "assignment",
    "customer",
    "target",
}
BOUNDARY_TERMS = {
    "verify",
    "verified",
    "evidence",
    "target",
    "tenant",
    "client",
    "specific",
    "not prove",
    "does not prove",
    "must not",
    "before",
    "fail",
    "closed",
    "reject",
    "hidden defaults",
}


def build_content_curation_report(
    items: list[KnowledgeItem],
    *,
    sample_size: int = 3,
) -> dict[str, Any]:
    """Build a deterministic per-pack sample of claim-level curation checks."""

    claims = _claim_rows(items)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        grouped[claim["pack_path"]].append(claim)

    samples: list[dict[str, Any]] = []
    for pack_path in sorted(grouped):
        pack_claims = sorted(grouped[pack_path], key=lambda row: row["claim_id"])
        samples.extend(_spread_sample(pack_claims, sample_size))

    samples = sorted(samples, key=lambda row: row["claim_id"])
    sampled_packs = {sample["pack_path"] for sample in samples}
    curation_needed = sum(
        1 for sample in samples if sample["review_decision"] == "curation_needed"
    )
    return {
        "status": "needs_curation" if curation_needed else "passed",
        "scope": {
            "mode": "sampling",
            "boundary": (
                "Content curation report is a deterministic sample of domain-pack "
                "claims, not exhaustive claim-by-claim SAP content certification. "
                "It complements repo-level gates by checking sampled source/access, "
                "freshness, evidence and tenant/customizing boundaries."
            ),
            "covered_by_repo_level_gates": [
                "schema validation",
                "runtime retrieval behavior",
                "source/access metadata presence",
                "CI/gate semantics",
                "from-zero ontology routing",
            ],
            "separate_pass_required_for": "full SAP claim accuracy curation",
        },
        "summary": {
            "total_claims": len(claims),
            "sampled_claims": len(samples),
            "total_packs_with_claims": len(grouped),
            "sampled_packs": len(sampled_packs),
            "sample_size_per_pack": sample_size,
            "curation_needed": curation_needed,
        },
        "samples": samples,
    }


def write_content_curation_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _claim_rows(items: list[KnowledgeItem]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda candidate: candidate.item_id):
        raw_claims = item.data.get("claims")
        claims = raw_claims if isinstance(raw_claims, list) else []
        for index, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict):
                continue
            statement = str(claim.get("statement") or "").strip()
            if not statement:
                continue
            row = _sample_row(item, claim, statement, index)
            rows.append(row)
    return rows


def _sample_row(
    item: KnowledgeItem, claim: dict[str, Any], statement: str, index: int
) -> dict[str, Any]:
    claim_id = f"{item.item_id}.{index:03d}"
    checks = _checks(item, claim, statement)
    decision = (
        "sample_passed"
        if all(check["status"] == "passed" for check in checks.values())
        else "curation_needed"
    )
    freshness = (
        item.data.get("freshness")
        if isinstance(item.data.get("freshness"), dict)
        else {}
    )
    return {
        "claim_id": claim_id,
        "item_id": item.item_id,
        "pack_path": str(item.path),
        "kind": item.kind,
        "access": item.access,
        "statement": statement,
        "evidence_ids": _strings(claim.get("evidence")),
        "source": _source_summary(item.data.get("source")),
        "freshness": freshness,
        "checks": checks,
        "review_decision": decision,
    }


def _checks(item: KnowledgeItem, claim: dict[str, Any], statement: str) -> dict[str, Any]:
    source = item.data.get("source") if isinstance(item.data.get("source"), dict) else {}
    freshness = (
        item.data.get("freshness")
        if isinstance(item.data.get("freshness"), dict)
        else {}
    )
    evidence_ids = _strings(claim.get("evidence"))
    statement_lower = statement.lower()
    tenant_tokens = set(statement_lower.replace("/", " ").split())
    tenant_sensitive = bool(TENANT_SENSITIVE_TERMS & tenant_tokens)
    boundary_present = not tenant_sensitive or any(
        term in statement_lower for term in BOUNDARY_TERMS
    )
    return {
        "source_access_boundary": _status(
            bool(source.get("kind"))
            and item.access in {"public", "gated", "internal_derived"},
            "source kind and item access are present",
            "missing source kind or invalid access metadata",
        ),
        "freshness_present": _status(
            all(freshness.get(key) for key in ["retrieved_at", "review_after"]),
            "freshness metadata includes retrieved_at and review_after",
            "freshness metadata is incomplete",
        ),
        "evidence_present": _status(
            bool(evidence_ids),
            "claim has evidence ids/pointers",
            "claim lacks evidence ids/pointers",
        ),
        "claim_scope_boundary": _status(
            boundary_present,
            "tenant/customizing-sensitive wording includes a boundary or is generic",
            "tenant/customizing-sensitive wording lacks explicit boundary",
        ),
    }


def _spread_sample(rows: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if sample_size <= 0 or len(rows) <= sample_size:
        return rows[: max(sample_size, 0)]
    if sample_size == 1:
        return [rows[0]]
    step = (len(rows) - 1) / (sample_size - 1)
    indexes = sorted({round(index * step) for index in range(sample_size)})
    return [rows[index] for index in indexes]


def _source_summary(value: Any) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    return {
        "kind": str(source.get("kind") or ""),
        "title": str(source.get("title") or ""),
        "url": str(source.get("url") or ""),
        "specificity": str(source.get("specificity") or ""),
    }


def _status(condition: bool, passed: str, failed: str) -> dict[str, str]:
    return {
        "status": "passed" if condition else "failed",
        "detail": passed if condition else failed,
    }


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
