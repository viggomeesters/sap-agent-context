from __future__ import annotations

from pathlib import Path

from sap_agent_context import repository


def test_load_items_reuses_yaml_parse_until_knowledge_file_changes(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    item_path = knowledge / "item.yaml"
    item_path.write_text(
        "id: sap.test.item\n"
        "kind: sap_app\n"
        "title: Test item\n"
        "access: public\n",
        encoding="utf-8",
    )

    calls = 0
    original = repository.read_yaml_mapping

    def counted_read(path: Path) -> dict:
        nonlocal calls
        calls += 1
        return original(path)

    monkeypatch.setattr(repository, "read_yaml_mapping", counted_read)
    repository.clear_load_items_cache()

    assert repository.load_items(tmp_path)[0].item_id == "sap.test.item"
    assert repository.load_items(tmp_path)[0].item_id == "sap.test.item"
    assert calls == 1

    item_path.write_text(
        "id: sap.test.changed\n"
        "kind: sap_app\n"
        "title: Changed item\n"
        "access: public\n",
        encoding="utf-8",
    )

    assert repository.load_items(tmp_path)[0].item_id == "sap.test.changed"
    assert calls == 2
