from __future__ import annotations

from pathlib import Path

from sap_agent_context import completeness


def test_matrix_loader_reuses_yaml_until_file_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    matrix = tmp_path / "matrix.yaml"
    matrix.write_text("scope: {id: first}\nminimums: {}\n", encoding="utf-8")
    reads = 0
    original_read_text = Path.read_text

    def counted_read_text(self: Path, *args, **kwargs):
        nonlocal reads
        if self == matrix:
            reads += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read_text)
    completeness._load_matrix_cached.cache_clear()

    first = completeness._load_matrix(matrix)
    second = completeness._load_matrix(matrix)

    assert first["scope"]["id"] == "first"
    assert second["scope"]["id"] == "first"
    assert reads == 1

    matrix.write_text("scope: {id: second}\nminimums: {}\n", encoding="utf-8")
    changed = completeness._load_matrix(matrix)

    assert changed["scope"]["id"] == "second"
    assert reads == 2
