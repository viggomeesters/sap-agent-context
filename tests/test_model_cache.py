from __future__ import annotations

from pathlib import Path

from sap_agent_context import model
from sap_agent_context.model import KnowledgeItem


def test_knowledge_item_retrieval_properties_are_cached(monkeypatch) -> None:
    calls = 0
    original_strings = model._strings

    def counted_strings(value):
        nonlocal calls
        calls += 1
        return original_strings(value)

    monkeypatch.setattr(model, "_strings", counted_strings)
    item = KnowledgeItem(
        path=Path("knowledge/test.yaml"),
        data={
            "id": "sap.test.item",
            "kind": "sap_app",
            "title": "Test item",
            "summary": "A reusable test item",
            "access": "public",
            "topics": ["equipment", "status"],
            "used_for": ["fo.workflow"],
            "claims": [{"statement": "Use it for a focused retrieval probe."}],
        },
    )

    assert item.topics == ["equipment", "status"]
    assert item.topics == ["equipment", "status"]
    assert item.used_for == ["fo.workflow"]
    assert item.used_for == ["fo.workflow"]
    first_text = item.text_for_retrieval
    second_text = item.text_for_retrieval

    assert first_text == second_text
    assert "sap.test.item" in first_text
    assert calls == 2
