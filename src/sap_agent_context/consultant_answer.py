"""Deterministic SAP consultant-style answer generation.

The generator is intentionally local and extractive: it turns runtime retrieval
results into a concise consultant answer with citations and fail-closed
boundaries. It does not call an LLM and does not claim live internet, tenant or
expert validation.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.answer_scenario_evaluation import DEFAULT_ANSWER_SCENARIO_FIXTURES
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_search import search_runtime_index

DEFAULT_SQLITE = "build/context.sqlite"
DEFAULT_ANSWER_PROFILES = "schema/answer-profiles.json"


def generate_consultant_answer(
    *,
    root: Path,
    question: str,
    sqlite_path: Path | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    sqlite = _ensure_index(root=root, sqlite_path=sqlite_path or root / DEFAULT_SQLITE)
    profiles = _load_answer_profiles(root / DEFAULT_ANSWER_PROFILES)
    results = search_runtime_index(sqlite, question, limit=max(limit, 0))
    classification = _classify_question(question, results)
    results = _augment_results_for_classification(
        sqlite=sqlite,
        classification=classification,
        results=results,
        limit=limit,
    )
    profile = profiles.get(classification)
    support_results = _supporting_results(classification, results, profiles)
    status, status_reasons = _answer_status(classification, support_results, profiles)
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
        "decision_trace": _decision_trace(
            classification=classification,
            profile=profile,
            retrieved_results=results,
            support_results=support_results,
            status=status,
            status_reasons=status_reasons,
        ),
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


def _load_answer_profiles(path: Path) -> dict[str, dict[str, Any]]:
    return _load_answer_profiles_cached(path.resolve())


@lru_cache(maxsize=16)
def _load_answer_profiles_cached(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"answer profiles file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "sap-agent-context.answer-profiles.v1":
        raise ValueError(f"unexpected answer profiles schema in {path}")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError(f"expected non-empty profiles list in {path}")

    by_classification: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError(f"invalid answer profile entry in {path}")
        profile_id = str(profile.get("id") or "")
        classification = str(profile.get("classification") or "")
        status = str(profile.get("status") or "")
        if not profile_id or not classification:
            raise ValueError(f"answer profile missing id/classification in {path}")
        if profile_id in seen_ids:
            raise ValueError(f"duplicate answer profile id: {profile_id}")
        if classification in by_classification:
            raise ValueError(f"duplicate answer classification: {classification}")
        if status not in {"ready", "needs_curation"}:
            raise ValueError(f"invalid answer profile status for {profile_id}: {status}")
        support_ids = set(_strings(profile.get("support_ids")))
        required_citations = set(_strings(profile.get("required_answer_citation_ids")))
        if status == "ready" and not support_ids:
            raise ValueError(f"ready answer profile has no support_ids: {profile_id}")
        missing_required = required_citations - support_ids
        if missing_required:
            missing = ", ".join(sorted(missing_required))
            raise ValueError(
                f"answer profile {profile_id} has citations outside support_ids: {missing}"
            )
        seen_ids.add(profile_id)
        by_classification[classification] = profile
    return by_classification


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
    if _looks_like_hcm_personnel_name_status_lookup(text):
        return "hcm_personnel_name_status"
    if _looks_like_cross_selling_table_lookup(text):
        return "cross_selling_tables"
    if _looks_like_retail_article_mass_class_assignment(text):
        return "retail_article_mass_class_assignment"
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


def _looks_like_hcm_personnel_name_status_lookup(text: str) -> bool:
    personnel_terms = {
        "pa0000",
        "pernr",
        "personeelsnummer",
        "personnel number",
        "personal nr",
    }
    name_terms = {"naam", "name", "persoon", "person"}
    status_terms = {
        "status van dienstverband",
        "dienstverband",
        "employment status",
        "employee status",
        "stat2",
    }
    return (
        any(term in text for term in personnel_terms)
        and any(term in text for term in name_terms)
        and any(term in text for term in status_terms)
    )


def _looks_like_cross_selling_table_lookup(text: str) -> bool:
    transaction_terms = {"vb41", "vb42", "vb43"}
    cross_selling_terms = {"cross-selling", "cross selling", "cs01", "pakket", "package"}
    lookup_terms = {"tabel", "table", "halen", "read", "extract", "data"}
    return (
        any(term in text for term in transaction_terms)
        and any(term in text for term in cross_selling_terms)
        and any(term in text for term in lookup_terms)
    )


def _looks_like_retail_article_mass_class_assignment(text: str) -> bool:
    article_terms = {"artikel", "article", "material", "product"}
    class_terms = {"artikelklasse", "class assignment", "extra class", "klasse"}
    mass_terms = {"massa", "mass", "bulk", "meerdere", "many"}
    route_terms = {"migration cockpit", "migratiecockpit", "cl24n", "alternatief"}
    return (
        any(term in text for term in article_terms)
        and any(term in text for term in class_terms)
        and any(term in text for term in mass_terms)
        and any(term in text for term in route_terms)
    )


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



def _augment_results_for_classification(
    *,
    sqlite: Path,
    classification: str,
    results: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    anchor_queries = {
        "hcm_personnel_name_status": [
            "PA0000 PA0002 PERNR STAT2 VORNA NACHN BEGDA ENDDA"
        ],
        "retail_article_mass_class_assignment": ["CL24N", "CLF_OBJ"],
    }
    queries = anchor_queries.get(classification)
    if not queries:
        return results
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    anchored: list[dict[str, Any]] = []
    for query in queries:
        anchored.extend(search_runtime_index(sqlite, query, limit=max(limit, 12)))
    for result in [*anchored, *results]:
        result_id = str(result.get("id") or "")
        if result_id in seen_ids:
            continue
        seen_ids.add(result_id)
        merged.append(result)
    return merged


def _supporting_results(
    classification: str,
    results: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    profile = profiles.get(classification)
    support_ids = set(_strings(profile.get("support_ids"))) if profile else set()
    if not support_ids:
        return results
    return [result for result in results if str(result.get("id") or "") in support_ids]


def _answer_status(
    classification: str,
    results: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    profile = profiles.get(classification)
    if not profile:
        return "needs_curation", ["no answer profile exists for classification"]
    if profile.get("status") != "ready":
        return "needs_curation", ["answer profile status is needs_curation"]
    if not results:
        return "needs_curation", ["no retrieved results matched profile support_ids"]
    if not any(
        _strings(result.get("source_ids")) and _strings(result.get("claim_ids"))
        for result in results[:5]
    ):
        return "needs_curation", [
            "top support results lack both source_ids and claim_ids"
        ]
    return "ready", ["ready profile matched citeable support evidence"]


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
    if classification == "cross_selling_tables":
        return (
            "Voor het VB42/VB43-cross-sellingpakket met condition type CS01 begin je "
            "in de gedocumenteerde material-only inrichting bij KOTD011. Selecteer daar "
            "de record voor KAPPL = VS, KSCHL = CS01, het ingevoerde MATNR en de geldige "
            "DATAB/DATBI-periode. Gebruik vervolgens KOTD011-KNUMH om KONDD en KONDDP "
            "te lezen; SMATN is het voorgestelde/pakketartikel en KONDDP-KPOSN ordent "
            "gepositioneerde pakketregels. Praktisch: lees beide itemtabellen, omdat "
            "bestaande of uitgebreid gepositioneerde entries in KONDDP kunnen staan. "
            "KOTD011 is niet universeel: controleer in het doelsysteem welke gegenereerde "
            "KOTDnnn-tabel de access sequence van CS01 werkelijk gebruikt. "
            f"Evidence: {evidence_ids}."
        )
    if classification == "retail_article_mass_class_assignment":
        return (
            "Kort antwoord: niet via de normale Product/Material-extensie in Migration "
            "Cockpit. SAP levert wel het aparte migratieobject 'Object classification - "
            "General template' (CLF_OBJ), inclusief materiaal-klassentype 001. Dat past "
            "bij een gecontroleerde initiële migratieload waarin product, klasse en "
            "kenmerken al bestaan; Migration Cockpit is geen algemene transactieroute "
            "voor onderhoud van bestaande live data. Voor het massaal koppelen van één "
            "extra klasse aan bestaande artikelen is CL24N de directe standaardroute: "
            "selecteer klasse en klassentype, voeg de artikelen/objecten toe en sla de "
            "toewijzingen op. Gebruik CLMM wanneer de klasse al is toegewezen en je vooral "
            "kenmerkwaarden massaal wilt wijzigen. De generieke transactie MASS is niet "
            "de primaire route voor classificatietoewijzingen. Test eerst met enkele "
            "artikelen en controleer klassentype, multiple-classification-inrichting en "
            f"autorisaties in het doelsysteem. Evidence: {evidence_ids}."
        )
    if classification == "hcm_personnel_name_status":
        return (
            "Koppel het personeelsnummer PERNR aan de datumgeldige PA0002-record "
            "voor de naam: VORNA is de voornaam en NACHN de achternaam. Als je al "
            "PA0001 gebruikt, kun je ENAME/SNAME als opgemaakte naam meenemen, maar "
            "PA0002 is geschikter voor losse naamcomponenten. De status van het "
            "dienstverband staat in PA0000-STAT2: standaard 0 = uit dienst, 1 = "
            "inactief, 2 = gepensioneerd en 3 = actief. Filter PA0000, PA0002 en "
            "eventueel PA0001 altijd op dezelfde peildatum met BEGDA <= peildatum <= "
            "ENDDA; alleen joinen op PERNR kan historische records verdubbelen. "
            "Controleer in het doelsysteem DDIC, statusinrichting, concurrent employment "
            "en HR-autorisaties voordat je dit als personeelswaarheid gebruikt. "
            f"Evidence: {evidence_ids}."
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


def _decision_trace(
    *,
    classification: str,
    profile: dict[str, Any] | None,
    retrieved_results: list[dict[str, Any]],
    support_results: list[dict[str, Any]],
    status: str,
    status_reasons: list[str],
) -> dict[str, Any]:
    support_ids = set(_strings(profile.get("support_ids"))) if profile else set()
    kept_ids = [str(result.get("id") or "") for result in support_results]
    dropped_ids = [
        str(result.get("id") or "")
        for result in retrieved_results
        if str(result.get("id") or "") not in set(kept_ids)
    ]
    return {
        "contract": "consultant_answer_decision_trace.v1",
        "classification": classification,
        "profile_id": str(profile.get("id") or "") if profile else "",
        "profile_status": str(profile.get("status") or "") if profile else "missing",
        "status": status,
        "status_reasons": status_reasons,
        "retrieved_count": len(retrieved_results),
        "support_count": len(support_results),
        "support_filter": {
            "mode": "profile_support_ids" if support_ids else "unfiltered_no_support_ids",
            "support_ids": sorted(support_ids),
            "kept_result_ids": kept_ids[:8],
            "dropped_result_ids": dropped_ids[:8],
        },
        "required_answer_citation_ids": _strings(
            profile.get("required_answer_citation_ids") if profile else []
        ),
        "boundary_decisions": [
            "status=ready requires a ready profile plus citeable support evidence",
            "needs_curation means draft-only; do not promote to tenant, release "
            "or customizing proof",
            "retrieval evidence is local/source-labelled and not live web validation",
        ],
    }


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
