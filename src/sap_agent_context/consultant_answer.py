"""Deterministic SAP consultant-style answer generation.

The generator is intentionally local and extractive: it turns runtime retrieval
results into a concise consultant answer with citations and fail-closed
boundaries. It does not call an LLM and does not claim live internet, tenant or
expert validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.answer_scenario_evaluation import DEFAULT_ANSWER_SCENARIO_FIXTURES
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

DEFAULT_SQLITE = "build/context.sqlite"
READY_CLASSIFICATIONS = {
    "analytics_extensibility",
    "integration_security",
    "material_fields",
    "mtart",
    "org_model",
    "p2p",
    "procurement_workflow",
}

CLASSIFICATION_SUPPORT_IDS: dict[str, set[str]] = {
    "analytics_extensibility": {
        "sap.app.custom-fields-and-logic-context",
        "sap.bulk.api.analytical-query.field-map",
        "sap.bulk.api.analytical-query.field-set",
        "sap.bulk.api.analytical-query.object",
        "sap.bulk.api.analytical-query.ref",
        "sap.bulk.api.analytical-query.rule",
    },
    "integration_security": {
        "sap.app.communication-arrangements-context",
        "sap.object.communication-arrangement-integration",
        "sap.pattern.integration.communication-arrangement-fo",
        "sap.policy.integration-no-secrets",
        "sap.field-map.integration-api-message-readiness",
    },
    "procurement_workflow": {
        "sap.app.manage-purchase-requisitions-context",
        "sap.app.manage-purchase-requisitions",
        "sap.bulk.control.procurement-sourcing.decision-rule",
        "sap.pattern.procurement-release-strategy-workflow-fo",
        "sap.rule.procurement-release-strategy-tenant-evidence",
        "sap.test-pattern.procurement-release-strategy-caveat",
    },
}


def generate_consultant_answer(
    *,
    root: Path,
    question: str,
    sqlite_path: Path | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    sqlite = _ensure_index(root=root, sqlite_path=sqlite_path or root / DEFAULT_SQLITE)
    results = search_runtime_index(sqlite, question, limit=max(limit, 0))
    classification = _classify_question(question, results)
    support_results = _supporting_results(classification, results)
    status = _answer_status(classification, support_results)
    answer = _answer_for_classification(classification, question, support_results, status)
    citations = _citations(support_results)
    boundary = {
        "live_web_validation": False,
        "expert_certification": False,
        "tenant_specific_truth": False,
        "message": (
            "This answer is generated from local source-labelled SAP Agent Context "
            "records. Verify target tenant, release and customizing evidence before "
            "implementation decisions."
        ),
    }
    return {
        "artifact_kind": "sap_consultant_answer",
        "status": status,
        "question": question,
        "answer": answer,
        "answer_style": "deterministic_extract_consultant_summary",
        "classification": classification,
        "citations": citations,
        "evidence": _evidence(support_results),
        "boundary": boundary,
        "contract": {
            "live_web_boundary": (
                "No live internet validation is performed by this command; external "
                "evidence must be checked separately."
            ),
            "answer_boundary": (
                "The prose answer summarizes retrieved context; it is not tenant/client-"
                "specific SAP configuration proof."
            ),
        },
    }


def evaluate_consultant_answers(
    *,
    root: Path,
    sqlite_path: Path | None = None,
    fixtures_path: Path | None = None,
) -> dict[str, Any]:
    sqlite = _ensure_index(root=root, sqlite_path=sqlite_path or root / DEFAULT_SQLITE)
    fixtures = _load_fixtures(fixtures_path or root / DEFAULT_ANSWER_SCENARIO_FIXTURES)
    results = [
        _evaluate_fixture(root=root, sqlite_path=sqlite, fixture=fixture)
        for fixture in fixtures
    ]
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "artifact_kind": "consultant_answer_evaluation_report",
        "status": "failed" if failures else "passed",
        "fixtures": len(results),
        "contract": {
            "purpose": "prove deterministic consultant prose keeps citations and boundaries",
            "live_web_boundary": "This gate does not perform live internet validation.",
        },
        "results": results,
    }


def _evaluate_fixture(root: Path, sqlite_path: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    question = str(fixture.get("question") or "")
    answer = generate_consultant_answer(
        root=root,
        question=question,
        sqlite_path=sqlite_path,
        limit=int(fixture.get("limit") or 12),
    )
    failures: list[str] = []
    expected_status = str(fixture.get("expected_answer_status") or "ready")
    if answer["status"] != expected_status:
        failures.append(f"expected status {expected_status}, got {answer['status']}")
    if not str(answer.get("answer") or "").strip():
        failures.append("answer text is empty")
    if not answer.get("citations"):
        failures.append("answer has no citations")
    if answer.get("boundary", {}).get("live_web_validation") is not False:
        failures.append("answer claims live web validation")
    if answer.get("boundary", {}).get("expert_certification") is not False:
        failures.append("answer claims expert certification")
    if answer.get("boundary", {}).get("tenant_specific_truth") is not False:
        failures.append("answer claims tenant-specific truth")
    if expected_status == "ready" and not _has_citable_support(answer):
        failures.append("ready answer has no citation with source_ids and claim_ids")
    if expected_status == "ready":
        cited_ids = {str(citation.get("id") or "") for citation in answer.get("citations") or []}
        for item_id in _strings(fixture.get("required_answer_citation_ids")):
            if item_id not in cited_ids:
                failures.append(f"required answer citation id missing: {item_id}")
    if expected_status == "needs_curation" and "needs curation" not in answer["answer"].lower():
        failures.append("needs_curation answer must say needs curation")
    for term in _strings(fixture.get("required_answer_terms")):
        if term.lower() not in _answer_text(answer):
            failures.append(f"required answer term missing: {term}")
    for terms in _mapping_of_string_lists(fixture.get("required_terms_by_id")).values():
        for term in terms:
            if term.lower() not in _answer_text(answer):
                failures.append(f"required by-id answer term missing: {term}")
    return {
        "id": str(fixture.get("id") or question),
        "question": question,
        "expected_answer_status": expected_status,
        "status": "failed" if failures else "passed",
        "answer_status": answer["status"],
        "classification": answer["classification"],
        "citation_count": len(answer["citations"]),
        "answer_excerpt": answer["answer"][:280],
        "failures": failures,
    }


def _ensure_index(*, root: Path, sqlite_path: Path) -> Path:
    if not sqlite_path.exists():
        items = load_items(root)
        build_indexes(
            items,
            sqlite_path=sqlite_path,
            jsonl_path=root / "build/items.jsonl",
            vector_jsonl_path=root / "build/vector-corpus.jsonl",
            root=root,
        )
    return sqlite_path


def _classify_question(question: str, results: list[dict[str, Any]]) -> str:
    text = question.lower()
    del results
    if _looks_like_unsupported_tenant_configuration(text):
        return "unsupported_configuration"
    if "module" in text:
        return "modules"
    if "mtart" in text:
        return "mtart"
    if "matnr" in text or "mara" in text:
        return "material_fields"
    if "purchase to pay" in text or "procure to pay" in text or "p2p" in text:
        return "p2p"
    if "organisatie" in text or "organization" in text:
        return "org_model"
    if _looks_like_integration_security(text):
        return "integration_security"
    if _looks_like_analytics_extensibility(text):
        return "analytics_extensibility"
    if _looks_like_procurement_workflow(text):
        return "procurement_workflow"
    return "generic"


def _looks_like_integration_security(text: str) -> bool:
    integration_terms = {
        "api",
        "communicatie arrangement",
        "communication arrangement",
        "communication system",
        "integration",
    }
    security_terms = {
        "authentication",
        "credential",
        "credentials",
        "redactie",
        "redaction",
        "secret",
        "secrets",
        "security",
        "tenant url",
    }
    return any(term in text for term in integration_terms) and any(
        term in text for term in security_terms
    )


def _looks_like_analytics_extensibility(text: str) -> bool:
    analytics_terms = {"analytics", "analytical", "report", "reporting", "rapportage", "kpi"}
    extensibility_terms = {
        "custom field",
        "extension",
        "extensibility",
        "exposure",
        "publish",
    }
    return any(term in text for term in analytics_terms) and any(
        term in text for term in extensibility_terms
    )


def _looks_like_procurement_workflow(text: str) -> bool:
    procurement_terms = {
        "procurement",
        "purchase order",
        "purchase requisition",
    }
    workflow_terms = {
        "approval",
        "approver",
        "flexible workflow",
        "release strategy",
        "threshold",
        "workflow",
    }
    return any(term in text for term in procurement_terms) and any(
        term in text for term in workflow_terms
    )


def _looks_like_unsupported_tenant_configuration(text: str) -> bool:
    tenant_terms = {
        "tenant",
        "go-live",
        "golive",
        "configure",
        "configuration",
        "configuring",
    }
    unsupported_domains = {"tax", "procedure", "fi tax", "pricing", "payroll"}
    return any(term in text for term in tenant_terms) and any(
        term in text for term in unsupported_domains
    )



def _supporting_results(classification: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    support_ids = CLASSIFICATION_SUPPORT_IDS.get(classification)
    if not support_ids:
        return results
    return [result for result in results if str(result.get("id") or "") in support_ids]

def _answer_status(classification: str, results: list[dict[str, Any]]) -> str:
    if classification not in READY_CLASSIFICATIONS:
        return "needs_curation"
    if not results:
        return "needs_curation"
    if not any(
        _strings(result.get("source_ids")) and _strings(result.get("claim_ids"))
        for result in results[:5]
    ):
        return "needs_curation"
    return "ready"


def _answer_for_classification(
    classification: str,
    question: str,
    results: list[dict[str, Any]],
    status: str,
) -> str:
    evidence_ids = ", ".join(str(result.get("id")) for result in results[:3])
    if classification == "mtart":
        return (
            "MTART is the material type field in the MARA material master context. "
            "For this repo's evidence surface, the relevant local anchor is the MARA "
            "DD03VT field catalog; answer using MARA.MTART, Material Type and the "
            "Dutch label Artikelsoort. Verify the target SAP release/tenant DDIC "
            f"metadata before treating this as implementation proof. Evidence: {evidence_ids}."
        )
    if classification == "material_fields":
        return (
            "For material-field questions, answer from DDIC field-catalog evidence. "
            "MARA.MATNR is present on the MARA material master catalog and EQUI.MATNR "
            "is present on the EQUI equipment master catalog; MTART is represented as "
            "MARA.MTART / Material Type / Artikelsoort. Use these as local evidence, "
            "then verify the target release/tenant dictionary before implementation. "
            f"Evidence: {evidence_ids}."
        )
    if classification == "org_model":
        return (
            "In SAP, organizational separation should be explained through multiple "
            "lenses rather than one magic hierarchy: company code, plant, purchasing "
            "organization and sales organization can separate legal, logistics, buying "
            "and sales responsibilities. Treat public/generic org context as answer "
            "guidance only; target tenant assignments and customizing need explicit "
            f"evidence. Evidence: {evidence_ids}."
        )
    if classification == "p2p":
        return (
            "Purchase-to-pay / procure-to-pay is the procurement process lens from "
            "buying need through purchasing and follow-on supplier invoice/payment "
            "readiness. In this local context, anchor the explanation on the P2P "
            "process lens and purchasing organization evidence, then verify target "
            f"workflow, release and customizing before final advice. Evidence: {evidence_ids}."
        )
    if classification == "integration_security":
        return (
            "For integration and communication-arrangement security, answer from the "
            "local integration evidence and keep public bundles secret-free/no secrets: "
            "name the communication arrangement, communication arrangements/system, "
            "authentication pattern, API or message surface, redaction requirements, "
            "and test evidence, but do not include "
            "tenant URLs, credentials, certificates or customer payloads. Verify the "
            f"target tenant setup before implementation. Evidence: {evidence_ids}."
        )
    if classification == "analytics_extensibility":
        return (
            "For analytics/extensibility questions, separate Custom Fields and Logic custom-field "
            "definition from exposure and consumption: confirm business context, publish/exposure "
            "status, analytical query or report/KPI surface, API/reporting consumers, "
            "filter/freshness evidence and tenant-specific availability. Treat the "
            "local records as source-labelled guidance, not target-system proof. "
            f"Evidence: {evidence_ids}."
        )
    if classification == "procurement_workflow":
        return (
            "For procurement release strategy or flexible-workflow questions, identify "
            "the purchase-requisition/purchasing process surface, owner approval, approver "
            "responsibilities, threshold or condition evidence, fallback/escalation path "
            "and test cases. Keep role/workflow behavior fail-closed until the target "
            f"tenant, release and customizing are verified. Evidence: {evidence_ids}."
        )
    if classification == "modules":
        return (
            "This question needs curation before a final exhaustive answer. The repo can "
            "explain SAP through foundation, landscape, process and source lenses, but it "
            "does not currently certify a complete module taxonomy. Give a caveated overview "
            "only, then add source-backed module coverage before claiming completeness. "
            f"Evidence: {evidence_ids}."
        )
    if classification == "unsupported_configuration":
        return (
            "This question needs curation before a safe consultant answer. It asks for "
            "tenant/release/configuration-specific guidance that the local retrieved "
            "context does not prove. Add source-backed target-system evidence before "
            f"answering as ready. Evidence: {evidence_ids or 'none'}."
        )
    if classification == "generic":
        return (
            "This question needs curation before a safe consultant answer. The current "
            "deterministic consultant-answer layer is intentionally narrow and only "
            "generates ready prose for covered scenario intents such as MARA/MTART/MATNR, "
            "organization separation, purchase/procure-to-pay, integration security, "
            "analytics/extensibility and procurement workflow. Add a source-backed "
            "foundation answer contract before answering this generic question. "
            f"Evidence: {evidence_ids or 'none'}."
        )
    result_summaries = "; ".join(
        f"{result.get('id')}: {result.get('text') or result.get('title')}" for result in results[:3]
    )
    return (
        f"Answer the question from the retrieved SAP Agent Context evidence. Status: {status}. "
        f"Use the cited records and keep tenant/release/customizing claims fail-closed. "
        f"Evidence: {result_summaries}."
    )


def _citations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for result in results[:8]:
        citations.append(
            {
                "id": str(result.get("id") or ""),
                "title": str(result.get("title") or ""),
                "kind": str(result.get("kind") or ""),
                "source_ids": _strings(result.get("source_ids")),
                "claim_ids": _strings(result.get("claim_ids")),
                "access": str(result.get("explain", {}).get("access") or ""),
            }
        )
    return citations


def _has_citable_support(answer: dict[str, Any]) -> bool:
    for citation in answer.get("citations") or []:
        if not isinstance(citation, dict):
            continue
        if citation.get("source_ids") and citation.get("claim_ids"):
            return True
    return False


def _evidence(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for rank, result in enumerate(results[:5], start=1):
        evidence.append(
            {
                "rank": rank,
                "id": str(result.get("id") or ""),
                "kind": str(result.get("kind") or ""),
                "matched_terms": _strings(result.get("explain", {}).get("matched_terms")),
                "rank_source": str(result.get("explain", {}).get("rank_source") or ""),
            }
        )
    return evidence


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"expected fixtures list in {path}")
    return [fixture for fixture in fixtures if isinstance(fixture, dict)]


def _answer_text(answer: dict[str, Any]) -> str:
    return str(answer.get("answer") or "").lower()


def _mapping_of_string_lists(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, raw_terms in value.items():
        terms = _strings(raw_terms)
        if terms:
            result[str(key)] = terms
    return result


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
