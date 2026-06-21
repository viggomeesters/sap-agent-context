"""Core data model helpers for SAP FO knowledge items."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_ACCESS = {"public", "gated", "internal_derived"}
ALLOWED_STATUS = {"active", "draft", "deprecated"}
ALLOWED_KINDS = {
    "access_policy",
    "decision_rule",
    "external_reference",
    "field_map",
    "fo_pattern",
    "sap_app",
    "sap_object",
    "sap_role",
    "scope_item",
    "test_pattern",
}


@dataclass(frozen=True)
class KnowledgeItem:
    """Loaded knowledge item with its repository path."""

    path: Path
    data: dict[str, Any]

    @property
    def item_id(self) -> str:
        return str(self.data["id"])

    @property
    def title(self) -> str:
        return str(self.data["title"])

    @property
    def kind(self) -> str:
        return str(self.data["kind"])

    @property
    def summary(self) -> str:
        return str(self.data.get("summary") or "")

    @property
    def access(self) -> str:
        return str(self.data["access"])

    @property
    def topics(self) -> list[str]:
        return _strings(self.data.get("topics"))

    @property
    def used_for(self) -> list[str]:
        return _strings(self.data.get("used_for"))

    @property
    def text_for_retrieval(self) -> str:
        raw_claims = self.data.get("claims")
        claims = raw_claims if isinstance(raw_claims, list) else []
        claim_text = " ".join(
            str(claim.get("statement") or "") for claim in claims if isinstance(claim, dict)
        )
        return " ".join(
            part
            for part in [
                self.item_id,
                self.title,
                self.kind,
                self.summary,
                " ".join(self.topics),
                " ".join(self.used_for),
                claim_text,
            ]
            if part
        )


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
