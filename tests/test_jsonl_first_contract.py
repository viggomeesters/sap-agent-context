from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
TEXT_PATHS = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / "schema").glob("*.yaml")),
]
FORBIDDEN_YAML_SSOT_PHRASES = [
    "YAML context and schema files remain the source of truth",
    "canonical source of truth remains YAML",
    "The canonical source of truth remains YAML",
    "YAML SSOT",
    "yaml_context",
    "knowledge/**/*.yaml and schema/**/*.yaml",
    "current YAML knowledge stays green",
    "YAML knowledge stays green",
    "YAML remains the temporary editing source",
    "YAML knowledge files remain the temporary editing source",
]


def test_repo_text_does_not_claim_yaml_source_of_truth() -> None:
    offenders: list[str] = []
    for path in TEXT_PATHS:
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_YAML_SSOT_PHRASES:
            if phrase in text:
                offenders.append(f"{path.relative_to(ROOT)}: {phrase}")

    assert not offenders


def test_docs_state_jsonl_first_with_yaml_as_legacy_authoring_import() -> None:
    doc = (ROOT / "docs" / "jsonl-record-surface.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    combined = doc + "\n" + readme

    required = [
        "records/*.jsonl is the canonical agent record surface",
        "JSONL-first",
        "YAML is a legacy authoring/import format",
        "JSONL -> build/context.sqlite",
        "Do not add new YAML-first source-of-truth language",
    ]
    for phrase in required:
        assert phrase in combined


def test_read_model_metadata_is_jsonl_primary_not_yaml_editing_source(tmp_path: Path) -> None:
    report = build_indexes(
        load_items(ROOT),
        sqlite_path=tmp_path / "context.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
    )

    assert report["read_model"]["source_of_truth"] == "records/*.jsonl"
    assert report["read_model"]["authoring_format"] == "legacy_yaml_import"
    assert "editing_source" not in report["read_model"]
    with sqlite3.connect(tmp_path / "context.sqlite") as conn:
        metadata = dict(conn.execute("SELECT key, value FROM read_model_metadata"))

    assert metadata["source_of_truth"] == "records/*.jsonl"
    assert metadata["authoring_format"] == "legacy_yaml_import"
    assert "editing_source" not in metadata

    item_record = json.loads((tmp_path / "items.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert "source_path" in item_record
