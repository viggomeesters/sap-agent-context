"""Filesystem loading for canonical YAML knowledge items."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from sap_agent_context.model import KnowledgeItem

DEFAULT_KNOWLEDGE_DIR = "knowledge"
SAFE_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
KnowledgeFingerprint = tuple[tuple[str, int, int], ...]


def load_items(root: Path) -> list[KnowledgeItem]:
    """Load all canonical YAML knowledge items below ``root/knowledge``.

    YAML parsing dominates the test/runtime feedback loop. Cache parsed items per
    repository root and invalidate when the knowledge file path/mtime/size
    fingerprint changes. Return a fresh list so callers can reorder/filter
    without mutating the cached list object.
    """
    resolved_root = root.resolve()
    knowledge_dir = resolved_root / DEFAULT_KNOWLEDGE_DIR
    fingerprint = _knowledge_fingerprint(knowledge_dir)
    return list(_load_items_cached(str(resolved_root), fingerprint))


def clear_load_items_cache() -> None:
    """Clear the repository loader cache.

    Primarily useful for tests and long-lived agent processes that intentionally
    edit the knowledge tree and want to force a reload before filesystem mtimes
    settle.
    """
    _load_items_cached.cache_clear()


@lru_cache(maxsize=8)
def _load_items_cached(root: str, fingerprint: KnowledgeFingerprint) -> tuple[KnowledgeItem, ...]:
    del fingerprint  # cache key only; files are read from root below
    knowledge_dir = Path(root) / DEFAULT_KNOWLEDGE_DIR
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
    return tuple(items)


def _knowledge_fingerprint(knowledge_dir: Path) -> KnowledgeFingerprint:
    if not knowledge_dir.exists():
        raise FileNotFoundError(f"knowledge directory not found: {knowledge_dir}")
    return tuple(
        (str(path.relative_to(knowledge_dir)), path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(knowledge_dir.rglob("*.yaml"))
    )


def read_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=SAFE_YAML_LOADER)
    payload = payload or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return payload
