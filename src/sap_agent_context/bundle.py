"""Context bundle generation for downstream FO tools."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sap_agent_context.model import KnowledgeItem

QUERY_SYNONYMS = {
    "factuur": "invoice",
    "facturen": "invoice",
    "goedkeuring": "approval",
    "goedkeuren": "approval",
    "leverancier": "supplier",
    "leveranciers": "supplier",
    "veldmapping": "field mapping",
    "stamdata": "master data",
    "autorisatie": "authorization",
    "autorisaties": "authorization",
    "formulier": "form",
    "uitvoer": "output",
    "migratie": "migration",
    "inkoop": "procurement",
}

PRECISION_TOKEN_THRESHOLD = 0.6


def build_context_bundle(
    items: list[KnowledgeItem],
    *,
    root: Path,
    intent: str,
    topic: str,
    sap_product: str = "",
    limit: int = 8,
    current_date: date | None = None,
) -> dict[str, Any]:
    today = current_date or date.today()
    ranked = _rank_items(items, intent=intent, topic=topic, sap_product=sap_product)
    selected = _assemble_bundle(items, ranked=ranked, intent=intent, limit=limit)
    bundle_items = [
        _bundle_item(item, root=root, current_date=today, score=score) for score, item in selected
    ]
    gaps = _bundle_gaps(bundle_items, intent=intent, topic=topic)
    status = "ready" if bundle_items and not gaps else "needs_curation"
    quality_signals = _quality_signals(bundle_items, gaps=gaps)
    return {
        "schema_version": 1,
        "bundle_kind": "sap_fo_context_bundle",
        "producer": {
            "name": "sap-agent-context",
            "contract": "sap-agent-context-bundle",
            "compatibility_bundle_kind": "sap_fo_context_bundle",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": {
            "intent": intent,
            "topic": topic,
            "sap_product": sap_product,
            "limit": limit,
        },
        "status": status,
        "items": bundle_items,
        "citations": _citations(bundle_items),
        "gaps": gaps,
        "quality_signals": quality_signals,
        "mccoy_integration": {
            "provider_type": "local-folder",
            "recommended_title": f"SAP Agent Context bundle - {topic}",
            "register_as": "local_folder",
            "reason": (
                "Curated SAP agent context bundle with source pointers, freshness "
                "and access labels."
            ),
        },
    }


def _rank_items(
    items: list[KnowledgeItem],
    *,
    intent: str,
    topic: str,
    sap_product: str,
) -> list[tuple[int, KnowledgeItem]]:
    intent_tokens = _tokens(intent)
    topic_tokens = _tokens(topic)
    product = sap_product.strip().lower()
    ranked = []
    for item in items:
        text = item.text_for_retrieval.lower()
        topic_score = sum(8 for token in topic_tokens if token in text)
        if not topic_score:
            continue
        score = 0
        score += topic_score
        score += sum(4 for token in intent_tokens if token in text)
        score += sum(8 for used_for in item.used_for if intent.lower() in used_for.lower())
        if product and str(item.data.get("sap_product") or "").lower() == product:
            score += 6
        if item.data.get("status") == "active":
            score += 2
        if score:
            ranked.append((score, item))
    return sorted(ranked, key=lambda pair: (-pair[0], pair[1].item_id))


def _assemble_bundle(
    items: list[KnowledgeItem],
    *,
    ranked: list[tuple[int, KnowledgeItem]],
    intent: str,
    limit: int,
) -> list[tuple[int, KnowledgeItem]]:
    selected: list[tuple[int, KnowledgeItem]] = ranked[:limit]
    selected_ids = {item.item_id for _, item in selected}
    by_id = {item.item_id: item for item in items}

    for _, item in list(selected):
        for related_id in _relation_ids(item):
            if len(selected) >= limit:
                break
            related = by_id.get(related_id)
            if related and related.item_id not in selected_ids:
                selected.append((1, related))
                selected_ids.add(related.item_id)

    required_kinds = _required_kinds_for_intent(intent)
    present_kinds = {item.kind for _, item in selected}
    selected_topic_tokens = set()
    for _, item in selected:
        selected_topic_tokens.update(_tokens(" ".join(item.topics)))

    for required_kind in sorted(required_kinds - present_kinds):
        candidate = _best_kind_candidate(ranked, required_kind, selected_ids, selected_topic_tokens)
        if candidate is None:
            continue
        selected.append(candidate)
        selected_ids.add(candidate[1].item_id)
    return selected


def _relation_ids(item: KnowledgeItem) -> list[str]:
    raw_relations = item.data.get("relations")
    relations: dict[str, Any] = raw_relations if isinstance(raw_relations, dict) else {}
    ids = []
    for value in relations.values():
        if isinstance(value, list):
            ids.extend(str(entry) for entry in value if str(entry).startswith("sap."))
    return ids


def _best_kind_candidate(
    ranked: list[tuple[int, KnowledgeItem]],
    required_kind: str,
    selected_ids: set[str],
    selected_topic_tokens: set[str],
) -> tuple[int, KnowledgeItem] | None:
    for score, item in ranked:
        if item.kind != required_kind or item.item_id in selected_ids:
            continue
        if selected_topic_tokens.intersection(_tokens(" ".join(item.topics))):
            return score, item
    return None


def _bundle_item(
    item: KnowledgeItem,
    *,
    root: Path,
    current_date: date,
    score: int,
) -> dict[str, Any]:
    raw_freshness = item.data.get("freshness")
    freshness: dict[str, Any] = raw_freshness if isinstance(raw_freshness, dict) else {}
    review_after = _parse_date(freshness.get("review_after"))
    expires_at = _parse_date(freshness.get("expires_at"))
    raw_source = item.data.get("source")
    source: dict[str, Any] = raw_source if isinstance(raw_source, dict) else {}
    return {
        "id": item.item_id,
        "title": item.title,
        "kind": item.kind,
        "score": score,
        "summary": item.summary,
        "topics": item.topics,
        "used_for": item.used_for,
        "access": item.access,
        "requires_login": bool(item.data.get("requires_login")),
        "sap_product": item.data.get("sap_product"),
        "path": str(item.path.relative_to(root)),
        "review_after": str(freshness.get("review_after") or ""),
        "expires_at": str(freshness.get("expires_at") or ""),
        "stale": bool(review_after and review_after < current_date),
        "expired": bool(expires_at and expires_at < current_date),
        "source": {
            "kind": source.get("kind"),
            "title": source.get("title"),
            "url": source.get("url", ""),
            "retrieved_at": source.get("retrieved_at"),
            "license_note": source.get("license_note"),
        },
        "claims": item.data.get("claims", []),
        "relations": item.data.get("relations", {}),
    }


def _citations(bundle_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    citations = []
    for item in bundle_items:
        raw_source = item.get("source")
        source: dict[str, Any] = raw_source if isinstance(raw_source, dict) else {}
        citations.append(
            {
                "item_id": str(item["id"]),
                "title": str(source.get("title") or item["title"]),
                "url": str(source.get("url") or ""),
                "access": str(item["access"]),
                "retrieved_at": str(source.get("retrieved_at") or ""),
            }
        )
    return citations


def _quality_signals(bundle_items: list[dict[str, Any]], *, gaps: list[str]) -> dict[str, Any]:
    kind_counts: dict[str, int] = {}
    access_labels = set()
    source_url_count = 0
    stale_count = 0
    expired_count = 0
    for item in bundle_items:
        kind = str(item.get("kind") or "")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        access = str(item.get("access") or "")
        if access:
            access_labels.add(access)
        if item.get("stale"):
            stale_count += 1
        if item.get("expired"):
            expired_count += 1
        raw_source = item.get("source")
        source: dict[str, Any] = raw_source if isinstance(raw_source, dict) else {}
        if str(source.get("url") or "").strip():
            source_url_count += 1
    return {
        "gap_count": len(gaps),
        "stale_count": stale_count,
        "expired_count": expired_count,
        "gated_item_count": sum(1 for item in bundle_items if item.get("access") == "gated"),
        "source_url_count": source_url_count,
        "access_labels": sorted(access_labels),
        "item_kind_counts": dict(sorted(kind_counts.items())),
    }


def _bundle_gaps(bundle_items: list[dict[str, Any]], *, intent: str, topic: str) -> list[str]:
    if not bundle_items:
        return [f"No curated SAP context found for intent={intent!r}, topic={topic!r}."]
    gaps = []
    gaps.extend(_topic_precision_gaps(bundle_items, topic=topic))
    if not any(item["kind"] == "test_pattern" for item in bundle_items):
        gaps.append("No test_pattern item selected; FO test section may need manual enrichment.")
    if not any(item["kind"] == "sap_app" for item in bundle_items):
        gaps.append("No sap_app item selected; SAP configuration section may be too generic.")
    if not any(item["kind"] == "sap_object" for item in bundle_items):
        gaps.append("No sap_object item selected; FO object scope may be too generic.")
    if not any(item["kind"] == "field_map" for item in bundle_items):
        gaps.append("No field_map item selected; FO field mapping may be too generic.")
    if not any(item["access"] == "public" for item in bundle_items):
        gaps.append(
            "Only gated/internal sources selected; citations may need consultant verification."
        )
    if "authorization" in intent and not any(item["kind"] == "sap_role" for item in bundle_items):
        gaps.append("No sap_role item selected; authorization impact may be too generic.")
    if "authorization" in intent and not any(
        item["kind"] == "access_policy" for item in bundle_items
    ):
        gaps.append("No access_policy item selected; access governance may be too weak.")
    if any(item["stale"] for item in bundle_items):
        gaps.append("One or more selected items are past review_after and need recertification.")
    if any(item["expired"] for item in bundle_items):
        gaps.append("One or more selected items are past expires_at and must not be used.")
    return gaps


def mccoy_provider_manifest(bundle_path: Path, *, title: str | None = None) -> dict[str, Any]:
    return {
        "type": "local-folder",
        "title": title or "SAP Agent Context bundle",
        "path": str(bundle_path.parent),
        "url": "",
        "provenance": "sap-agent-context",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "reason": (
            "Register this generated context bundle directory as a local SAP source provider."
        ),
        "bundle_file": str(bundle_path),
        "mccoy_command": (
            "uv run fo-gen-v2 register-source <workspace> <project-id> "
            f"--type local-folder --title {quote(title or 'SAP Agent Context bundle')} "
            f"--path {quote(str(bundle_path.parent))} --provenance sap-agent-context"
        ),
    }


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _tokens(value: str) -> set[str]:
    raw_tokens = {
        part for part in value.lower().replace("-", " ").replace("_", " ").split() if len(part) > 2
    }
    expanded = set(raw_tokens)
    for token in raw_tokens:
        expanded.update(QUERY_SYNONYMS.get(token, "").split())
    return {token for token in expanded if len(token) > 2}


def _precision_tokens(value: str) -> set[str]:
    tokens = set()
    for token in _tokens(value):
        translated = QUERY_SYNONYMS.get(token)
        if translated:
            tokens.update(part for part in translated.split() if len(part) > 2)
        else:
            tokens.add(token)
    generic = {
        "sap",
        "s4hana",
        "cloud",
        "public",
        "edition",
        "functioneel",
        "ontwerp",
    }
    return tokens - generic


def _topic_precision_gaps(bundle_items: list[dict[str, Any]], *, topic: str) -> list[str]:
    topic_tokens = _precision_tokens(topic)
    if len(topic_tokens) < 3:
        return []

    best_overlap = 0
    best_item_id = ""
    for item in bundle_items:
        item_text = " ".join(
            str(part)
            for part in [
                item.get("id"),
                item.get("title"),
                item.get("summary"),
                " ".join(str(topic) for topic in item.get("topics", [])),
                " ".join(str(used_for) for used_for in item.get("used_for", [])),
            ]
            if part
        )
        overlap = len(topic_tokens.intersection(_precision_tokens(item_text)))
        if overlap > best_overlap:
            best_overlap = overlap
            best_item_id = str(item.get("id") or "")

    precision = best_overlap / len(topic_tokens)
    if precision < PRECISION_TOKEN_THRESHOLD:
        return [
            (
                "Low topic precision; no selected item covers enough of the query "
                f"tokens ({best_overlap}/{len(topic_tokens)}, best_item={best_item_id})."
            )
        ]
    return []


def _required_kinds_for_intent(intent: str) -> set[str]:
    required = {"external_reference", "sap_app", "sap_object", "field_map", "test_pattern"}
    if "authorization" in intent:
        required.update({"sap_role", "access_policy"})
    return required


def quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
