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
SOURCE_SPECIFICITY_FOR_L2 = {"catalog_entry", "exact_page", "internal_pattern"}
SOURCE_SPECIFICITY_FOR_L3 = {"catalog_entry", "exact_page"}
MATURITY_LEVELS = {
    "L0": "blocked: one or more claim curation checks fail before agent use",
    "L1": "metadata-ready: source/access, freshness, evidence and boundary checks pass",
    "L2": (
        "agent-ready: L1 plus specific source posture, explicit confidence and usage "
        "constraints fit clone-local agent use"
    ),
    "L3": (
        "expert-ready: L2 plus explicit high confidence, structured expert review, "
        "exact/catalog public evidence and review-window completeness"
    ),
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
    maturity_distribution = _maturity_distribution(claims)
    sampled_maturity_distribution = _maturity_distribution(samples)
    maturity_blocked_claims = maturity_distribution.get("L0", 0)
    sampled_ids = {sample["claim_id"] for sample in samples}
    claim_maturity_index = [
        _maturity_index_row(claim, sampled=claim["claim_id"] in sampled_ids)
        for claim in sorted(claims, key=lambda row: row["claim_id"])
    ]
    return {
        "status": "needs_curation" if curation_needed or maturity_blocked_claims else "passed",
        "scope": {
            "mode": "sampling",
            "boundary": (
                "Content curation report is a deterministic sample of domain-pack "
                "claims, not exhaustive claim-by-claim SAP content certification. "
                "It complements repo-level gates by checking sampled source/access, "
                "freshness, evidence and tenant/customizing boundaries."
            ),
            "claim_maturity_boundary": (
                "L1/L2/L3 levels classify claim curation readiness for agent use. "
                "They do not certify SAP accuracy; L3 requires explicit expert/high-confidence "
                "curation evidence that generic repo gates cannot invent."
            ),
            "maturity_levels": MATURITY_LEVELS,
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
            "maturity_blocked_claims": maturity_blocked_claims,
            "maturity_distribution": maturity_distribution,
            "sampled_maturity_distribution": sampled_maturity_distribution,
            "lowest_maturity": _lowest_maturity(maturity_distribution),
            "next_maturity_target": _next_maturity_target(maturity_distribution),
        },
        "claim_maturity_index": claim_maturity_index,
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
    maturity = _claim_maturity(item, claim, checks)
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
    confidence = _explicit_confidence(item, claim)
    return {
        "claim_id": claim_id,
        "item_id": item.item_id,
        "pack_path": str(item.path),
        "kind": item.kind,
        "access": item.access,
        "statement": statement,
        "confidence": confidence,
        "confidence_present": confidence is not None,
        "evidence_ids": _strings(claim.get("evidence")),
        "source": _source_summary(item.data.get("source")),
        "freshness": freshness,
        "checks": checks,
        "maturity": maturity,
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


def _claim_maturity(
    item: KnowledgeItem, claim: dict[str, Any], checks: dict[str, Any]
) -> dict[str, Any]:
    source = item.data.get("source") if isinstance(item.data.get("source"), dict) else {}
    freshness = (
        item.data.get("freshness")
        if isinstance(item.data.get("freshness"), dict)
        else {}
    )
    confidence = _explicit_confidence(item, claim)
    usage_constraints = _strings(claim.get("usage_constraints")) + _strings(
        item.data.get("usage_constraints")
    )
    specificity = str(source.get("specificity") or "")
    source_kind = str(source.get("kind") or "")

    if not all(check["status"] == "passed" for check in checks.values()):
        return {
            "level": "L0",
            "status": "blocked",
            "reasons": [
                name for name, check in checks.items() if check["status"] != "passed"
            ],
            "next_step": (
                "Fix failed source/freshness/evidence/boundary checks before "
                "maturity promotion."
            ),
        }

    l2_conditions = {
        "specific_source_posture": specificity in SOURCE_SPECIFICITY_FOR_L2,
        "explicit_confidence_medium_or_high": confidence in {"medium", "high"},
        "usage_constraints_for_non_public": item.access == "public" or bool(usage_constraints),
    }
    if not all(l2_conditions.values()):
        return {
            "level": "L1",
            "status": "metadata_ready",
            "reasons": [key for key, passed in l2_conditions.items() if not passed],
            "next_step": (
                "Add source specificity, explicit confidence and usage constraints for "
                "agent-ready L2."
            ),
        }

    l3_conditions = {
        "confidence_high": confidence == "high",
        "public_exact_or_catalog_source": item.access == "public"
        and source_kind == "public_url"
        and specificity in SOURCE_SPECIFICITY_FOR_L3,
        "review_window_complete": all(
            freshness.get(key)
            for key in ["valid_from", "retrieved_at", "review_after", "expires_at"]
        ),
        "structured_expert_review_present": _has_structured_expert_review(claim),
    }
    if not all(l3_conditions.values()):
        return {
            "level": "L2",
            "status": "agent_ready",
            "reasons": [key for key, passed in l3_conditions.items() if not passed],
            "next_step": "Promote only with explicit expert/high-confidence curation evidence.",
        }

    return {
        "level": "L3",
        "status": "expert_ready",
        "reasons": [],
        "next_step": "Keep review_after/expires_at current; do not generalize beyond source scope.",
    }


def _maturity_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    distribution = {level: 0 for level in MATURITY_LEVELS}
    for row in rows:
        level = row.get("maturity", {}).get("level", "L0")
        distribution[level] = distribution.get(level, 0) + 1
    return distribution


def _lowest_maturity(distribution: dict[str, int]) -> str:
    for level in ["L0", "L1", "L2", "L3"]:
        if distribution.get(level, 0):
            return level
    return "L3"


def _next_maturity_target(distribution: dict[str, int]) -> str:
    if distribution.get("L0", 0):
        return "Fix L0 blocked claims to reach L1 metadata readiness."
    if distribution.get("L1", 0):
        return "Promote L1 claims to L2 by adding specific source posture and usage constraints."
    if distribution.get("L2", 0):
        return "Promote selected high-value L2 claims to L3 with explicit expert review evidence."
    return "Maintain L3 review windows and avoid new uncurated claims."


def _maturity_index_row(row: dict[str, Any], *, sampled: bool) -> dict[str, Any]:
    maturity = row["maturity"]
    return {
        "claim_id": row["claim_id"],
        "item_id": row["item_id"],
        "pack_path": row["pack_path"],
        "sampled": sampled,
        "level": maturity["level"],
        "status": maturity["status"],
        "reasons": maturity["reasons"],
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


def _explicit_confidence(item: KnowledgeItem, claim: dict[str, Any]) -> str | None:
    for source in [claim, item.data]:
        value = source.get("confidence")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


def _has_structured_expert_review(claim: dict[str, Any]) -> bool:
    curation = claim.get("curation")
    if not isinstance(curation, dict):
        return False
    expert_review = curation.get("expert_review")
    if not isinstance(expert_review, dict):
        return False
    return bool(
        expert_review.get("reviewed_at")
        and expert_review.get("reviewer_role")
        and expert_review.get("evidence_id")
        and str(expert_review.get("status") or "").lower() in {"reviewed", "approved"}
    )


def _status(condition: bool, passed: str, failed: str) -> dict[str, str]:
    return {
        "status": "passed" if condition else "failed",
        "detail": passed if condition else failed,
    }


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
