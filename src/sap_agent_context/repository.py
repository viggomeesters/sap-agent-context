"""Filesystem loading for canonical YAML knowledge items."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.model import KnowledgeItem

DEFAULT_KNOWLEDGE_DIR = "knowledge"


def load_items(root: Path) -> list[KnowledgeItem]:
    """Load all canonical YAML knowledge items below ``root/knowledge``."""
    knowledge_dir = root / DEFAULT_KNOWLEDGE_DIR
    if not knowledge_dir.exists():
        raise FileNotFoundError(f"knowledge directory not found: {knowledge_dir}")

    items: list[KnowledgeItem] = []
    for path in sorted(knowledge_dir.rglob("*.yaml")):
        payload = read_yaml_mapping(path)
        if isinstance(payload.get("items"), list):
            for index, raw_item in enumerate(payload["items"], start=1):
                if not isinstance(raw_item, dict):
                    raise ValueError(f"expected mapping in {path} items[{index}]")
                items.append(KnowledgeItem(path=path, data=raw_item))
            continue
        items.append(KnowledgeItem(path=path, data=payload))
    return items


def read_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return payload
