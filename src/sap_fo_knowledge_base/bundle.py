"""Context bundle generation for downstream FO tools."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sap_fo_knowledge_base.model import KnowledgeItem


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
    selected = ranked[:limit]
    bundle_items = [
        _bundle_item(item, root=root, current_date=today, score=score) for score, item in selected
    ]
    gaps = _bundle_gaps(bundle_items, intent=intent, topic=topic)
    return {
        "schema_version": 1,
        "bundle_kind": "sap_fo_context_bundle",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": {
            "intent": intent,
            "topic": topic,
            "sap_product": sap_product,
            "limit": limit,
        },
        "status": "ready" if bundle_items else "needs_curation",
        "items": bundle_items,
        "citations": _citations(bundle_items),
        "gaps": gaps,
        "mccoy_integration": {
            "provider_type": "local-folder",
            "recommended_title": f"SAP FO KB bundle - {topic}",
            "register_as": "local_folder",
            "reason": (
                "Curated SAP FO knowledge bundle with source pointers, freshness and access labels."
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
        score = 0
        score += sum(8 for token in topic_tokens if token in text)
        score += sum(4 for token in intent_tokens if token in text)
        score += sum(8 for used_for in item.used_for if intent.lower() in used_for.lower())
        if product and str(item.data.get("sap_product") or "").lower() == product:
            score += 6
        if item.data.get("status") == "active":
            score += 2
        if score:
            ranked.append((score, item))
    return sorted(ranked, key=lambda pair: (-pair[0], pair[1].item_id))


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
        "stale": bool(review_after and review_after < current_date),
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


def _bundle_gaps(bundle_items: list[dict[str, Any]], *, intent: str, topic: str) -> list[str]:
    if not bundle_items:
        return [f"No curated SAP FO knowledge found for intent={intent!r}, topic={topic!r}."]
    gaps = []
    if not any(item["kind"] == "test_pattern" for item in bundle_items):
        gaps.append("No test_pattern item selected; FO test section may need manual enrichment.")
    if not any(item["kind"] == "sap_app" for item in bundle_items):
        gaps.append("No sap_app item selected; SAP configuration section may be too generic.")
    if not any(item["access"] == "public" for item in bundle_items):
        gaps.append(
            "Only gated/internal sources selected; citations may need consultant verification."
        )
    if any(item["stale"] for item in bundle_items):
        gaps.append("One or more selected items are past review_after and need recertification.")
    return gaps


def mccoy_provider_manifest(bundle_path: Path, *, title: str | None = None) -> dict[str, Any]:
    return {
        "type": "local-folder",
        "title": title or "SAP FO Knowledge Base context bundle",
        "path": str(bundle_path.parent),
        "url": "",
        "provenance": "sap-fo-knowledge-base",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Register this generated KB bundle directory as a local FO source provider.",
        "bundle_file": str(bundle_path),
        "mccoy_command": (
            "uv run fo-gen-v2 register-source <workspace> <project-id> "
            f"--type local-folder --title {quote(title or 'SAP FO Knowledge Base context bundle')} "
            f"--path {quote(str(bundle_path.parent))} --provenance sap-fo-knowledge-base"
        ),
    }


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _tokens(value: str) -> set[str]:
    return {
        part for part in value.lower().replace("-", " ").replace("_", " ").split() if len(part) > 2
    }


def quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
