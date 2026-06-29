"""Agent-first JSONL record export and validation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sap_agent_context.model import KnowledgeItem

RECORD_FILES = {
    "apps": "apps.jsonl",
    "tables": "tables.jsonl",
    "fields": "fields.jsonl",
    "workflows": "workflows.jsonl",
    "roles": "roles.jsonl",
    "claims": "claims.jsonl",
    "sources": "sources.jsonl",
    "relations": "relations.jsonl",
}

KIND_TO_RECORD_FILE = {
    "sap_app": "apps",
    "sap_object": "tables",
    "sap_field": "fields",
    "sap_role": "roles",
    "access_policy": "workflows",
    "decision_rule": "workflows",
    "external_reference": "workflows",
    "field_map": "workflows",
    "fo_pattern": "workflows",
    "scope_item": "workflows",
    "test_pattern": "workflows",
}

RELATION_TYPE_BY_GROUP = {
    "apps": "uses_app",
    "fields": "has_field",
    "objects": "operates_on",
    "related_objects": "related_to",
    "rules": "uses_rule",
    "source_references": "source_for",
    "test_patterns": "tested_by",
}

SCHEMA_FILE_BY_RECORD_FILE = {
    "apps": "item.schema.json",
    "tables": "item.schema.json",
    "fields": "item.schema.json",
    "workflows": "item.schema.json",
    "roles": "item.schema.json",
    "claims": "claim.schema.json",
    "sources": "source.schema.json",
    "relations": "relation.schema.json",
}


def export_agent_records(
    items: list[KnowledgeItem],
    output_dir: Path,
    *,
    root: Path,
) -> dict[str, Any]:
    """Import legacy YAML authoring items into agent-first JSONL record files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in RECORD_FILES}

    for item in sorted(items, key=lambda item: item.item_id):
        grouped[KIND_TO_RECORD_FILE.get(item.kind, "workflows")].append(_item_record(item, root))
        grouped["sources"].append(_source_record(item))
        grouped["claims"].extend(_claim_records(item))
        grouped["relations"].extend(_relation_records(item))

    counts: dict[str, int] = {}
    for name, filename in RECORD_FILES.items():
        path = output_dir / filename
        _write_jsonl(path, grouped[name])
        counts[name] = len(grouped[name])

    return {
        "status": "exported",
        "legacy_authoring_source": "knowledge/**/*.yaml",
        "canonical_target": "records/*.jsonl",
        "output_dir": str(output_dir),
        "files": len(RECORD_FILES),
        "records": sum(counts.values()),
        "counts": counts,
    }


def validate_agent_records(records_dir: Path, *, schema_dir: Path) -> dict[str, Any]:
    """Validate exported JSONL records against the repo's lightweight JSON schema files."""
    issues: list[dict[str, str]] = []
    total = 0
    file_count = 0
    for name, filename in RECORD_FILES.items():
        path = records_dir / filename
        schema_path = schema_dir / SCHEMA_FILE_BY_RECORD_FILE[name]
        if not path.exists():
            issues.append({"path": str(path), "message": "record file is missing"})
            continue
        if not schema_path.exists():
            issues.append({"path": str(schema_path), "message": "schema file is missing"})
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        file_count += 1
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append({"path": str(path), "message": f"line {line_number}: {exc}"})
                continue
            issues.extend(_validate_record(record, schema, path, line_number))
    return {
        "status": "failed" if issues else "passed",
        "files": file_count,
        "records": total,
        "issues": issues,
    }


def validate_yaml_jsonl_roundtrip_compatibility(
    items: list[KnowledgeItem], records_dir: Path
) -> dict[str, Any]:
    """Check exported JSONL preserves the legacy YAML compatibility surface."""
    issues: list[dict[str, str]] = []
    records = _load_record_files(records_dir)
    item_records = {
        record["id"]: record
        for group in ("apps", "tables", "fields", "workflows", "roles")
        for record in records.get(group, [])
        if isinstance(record.get("id"), str)
    }
    claims_by_subject = _group_by(records.get("claims", []), "subject_id")
    sources_by_subject = _group_by(records.get("sources", []), "subject_id")
    relations_by_subject = _group_by(records.get("relations", []), "subject_id")

    for item in sorted(items, key=lambda value: value.item_id):
        record = item_records.get(item.item_id)
        if record is None:
            issues.append({"id": item.item_id, "message": "missing item record"})
            continue

        _compare_scalar(issues, item.item_id, record, "kind", item.kind)
        _compare_scalar(issues, item.item_id, record, "title", item.title)
        _compare_scalar(issues, item.item_id, record, "access", item.access)
        _compare_list(issues, item.item_id, record, "topics", item.topics)
        _compare_list(issues, item.item_id, record, "used_for", item.used_for)

        if not record.get("source_path"):
            issues.append({"id": item.item_id, "message": "source_path missing"})
        if not record.get("source_ids"):
            issues.append({"id": item.item_id, "message": "source_ids missing"})
        if not record.get("claim_ids") and item.data.get("claims"):
            issues.append({"id": item.item_id, "message": "claim_ids missing for YAML claims"})
        if not record.get("relation_ids") and item.data.get("relations"):
            issues.append(
                {"id": item.item_id, "message": "relation_ids missing for YAML relations"}
            )

        expected_claims = (
            item.data.get("claims") if isinstance(item.data.get("claims"), list) else []
        )
        if len(claims_by_subject.get(item.item_id, [])) != len(expected_claims):
            issues.append({"id": item.item_id, "message": "claim count changed during export"})

        if len(sources_by_subject.get(item.item_id, [])) != 1:
            issues.append({"id": item.item_id, "message": "expected exactly one source record"})

        relations = (
            item.data.get("relations")
            if isinstance(item.data.get("relations"), dict)
            else {}
        )
        expected_relations = sum(
            len(targets) for targets in relations.values() if isinstance(targets, list)
        )
        if len(relations_by_subject.get(item.item_id, [])) != expected_relations:
            issues.append({"id": item.item_id, "message": "relation count changed during export"})

    return {
        "status": "failed" if issues else "passed",
        "items": len(items),
        "records": sum(len(value) for value in records.values()),
        "issues": issues,
        "compatibility_note": (
            "YAML remains legacy import; JSONL preserves the compatibility surface "
            "needed for future JSONL-native authoring."
        ),
    }


def _item_record(item: KnowledgeItem, root: Path) -> dict[str, Any]:
    source_id = _source_id(item)
    return {
        "id": item.item_id,
        "kind": item.kind,
        "title": item.title,
        "summary": item.summary,
        "status": str(item.data.get("status") or ""),
        "access": item.access,
        "requires_login": bool(item.data.get("requires_login")),
        "sap_product": str(item.data.get("sap_product") or ""),
        "topics": _unique_strings(item.topics),
        "used_for": _unique_strings(item.used_for),
        "source_path": str(item.path.relative_to(root)),
        "source_ids": [source_id],
        "claim_ids": [record["id"] for record in _claim_records(item)],
        "relation_ids": [record["id"] for record in _relation_records(item)],
        "freshness": _freshness(item),
        "retrieval": {
            "keywords": _retrieval_keywords(item),
            "queries": _retrieval_queries(item),
            "negative_keywords": _strings_from_mapping(
                item.data.get("retrieval"), "negative_keywords"
            ),
        },
    }


def _source_record(item: KnowledgeItem) -> dict[str, Any]:
    source = item.data.get("source") if isinstance(item.data.get("source"), dict) else {}
    retrieved_at = source.get("retrieved_at") or _freshness(item).get("retrieved_at") or ""
    return {
        "id": _source_id(item),
        "subject_id": item.item_id,
        "kind": str(source.get("kind") or ""),
        "title": str(source.get("title") or ""),
        "url": str(source.get("url") or ""),
        "access": item.access,
        "requires_login": bool(item.data.get("requires_login")),
        "retrieved_at": str(retrieved_at),
        "specificity": str(source.get("specificity") or ""),
        "license_note": str(source.get("license_note") or ""),
    }


def _claim_records(item: KnowledgeItem) -> list[dict[str, Any]]:
    claims = item.data.get("claims") if isinstance(item.data.get("claims"), list) else []
    records: list[dict[str, Any]] = []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            continue
        confidence = claim.get("confidence") or item.data.get("confidence") or "medium"
        records.append(
            {
                "id": f"sap.claim.{_slug_id(item.item_id)}.{index:03d}",
                "subject_id": item.item_id,
                "statement": str(claim.get("statement") or ""),
                "confidence": str(confidence),
                "evidence_ids": [str(value) for value in claim.get("evidence") or []],
                "freshness": _freshness(item),
                "usage_constraints": _usage_constraints(item, claim),
            }
        )
    return records


def _relation_records(item: KnowledgeItem) -> list[dict[str, Any]]:
    relations = item.data.get("relations") if isinstance(item.data.get("relations"), dict) else {}
    records: list[dict[str, Any]] = []
    per_type_index: dict[str, int] = defaultdict(int)
    for group, targets in sorted(relations.items()):
        if not isinstance(targets, list):
            continue
        relation_type = RELATION_TYPE_BY_GROUP.get(str(group), str(group))
        for target in targets:
            target_id = str(target)
            if not target_id.strip():
                continue
            per_type_index[relation_type] += 1
            records.append(
                {
                    "id": (
                        f"sap.rel.{_slug_id(item.item_id)}."
                        f"{_slug_id(relation_type)}.{per_type_index[relation_type]:03d}"
                    ),
                    "subject_id": item.item_id,
                    "type": relation_type,
                    "target_id": target_id,
                    "source_ids": [_source_id(item)],
                }
            )
    return records


def _freshness(item: KnowledgeItem) -> dict[str, str]:
    freshness = item.data.get("freshness") if isinstance(item.data.get("freshness"), dict) else {}
    return {
        "valid_from": str(freshness.get("valid_from") or ""),
        "review_after": str(freshness.get("review_after") or ""),
        "expires_at": str(freshness.get("expires_at") or ""),
        "retrieved_at": str(freshness.get("retrieved_at") or ""),
    }


def _retrieval_keywords(item: KnowledgeItem) -> list[str]:
    retrieval = item.data.get("retrieval") if isinstance(item.data.get("retrieval"), dict) else {}
    keywords = _strings_from_mapping(retrieval, "keywords")
    return _unique_strings(
        [item.item_id, item.title, item.kind, *item.topics, *item.used_for, *keywords]
    )


def _retrieval_queries(item: KnowledgeItem) -> list[str]:
    retrieval = item.data.get("retrieval") if isinstance(item.data.get("retrieval"), dict) else {}
    queries = _strings_from_mapping(retrieval, "queries")
    return queries or [item.title]


def _usage_constraints(item: KnowledgeItem, claim: dict[str, Any]) -> list[str]:
    constraints = _strings_from_mapping(claim, "usage_constraints")
    constraints.extend(_strings_from_mapping(item.data, "usage_constraints"))
    if item.access == "internal_derived" and not constraints:
        constraints.append(
            "Verify this internal-derived context in the target SAP tenant/system before "
            "treating it as customer-specific proof."
        )
    return _unique_strings(constraints)


def _source_id(item: KnowledgeItem) -> str:
    if item.kind == "external_reference":
        return item.item_id
    return f"sap.source.{_slug_id(item.item_id)}"


def _slug_id(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")


def _strings_from_mapping(value: Any, key: str) -> list[str]:
    if not isinstance(value, dict):
        return []
    raw = value.get(key)
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in sorted(records, key=lambda record: str(record["id"])):
            handle.write(json.dumps(record, sort_keys=True, default=str, ensure_ascii=False) + "\n")


def _load_record_files(records_dir: Path) -> dict[str, list[dict[str, Any]]]:
    loaded: dict[str, list[dict[str, Any]]] = {}
    for name, filename in RECORD_FILES.items():
        path = records_dir / filename
        loaded[name] = []
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                loaded[name].append(json.loads(line))
    return loaded


def _group_by(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get(key) or "")].append(record)
    return grouped


def _compare_scalar(
    issues: list[dict[str, str]], item_id: str, record: dict[str, Any], field: str, expected: str
) -> None:
    if str(record.get(field) or "") != str(expected or ""):
        issues.append({"id": item_id, "message": f"{field} changed during export"})


def _compare_list(
    issues: list[dict[str, str]],
    item_id: str,
    record: dict[str, Any],
    field: str,
    expected: list[str],
) -> None:
    if _unique_strings(record.get(field) or []) != _unique_strings(expected):
        issues.append({"id": item_id, "message": f"{field} changed during export"})


def _validate_record(
    record: dict[str, Any],
    schema: dict[str, Any],
    path: Path,
    line_number: int,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    for field in required:
        if field not in record:
            issues.append({"path": str(path), "message": f"line {line_number}: missing {field}"})
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field, rules in properties.items():
        if field not in record or not isinstance(rules, dict):
            continue
        value = record[field]
        expected_type = rules.get("type")
        if expected_type and not _matches_type(value, str(expected_type)):
            issues.append(
                {
                    "path": str(path),
                    "message": f"line {line_number}: {field} must be {expected_type}",
                }
            )
        enum = rules.get("enum")
        if isinstance(enum, list) and value not in enum:
            issues.append(
                {"path": str(path), "message": f"line {line_number}: {field} must be one of {enum}"}
            )
        has_min_items = rules.get("minItems") and isinstance(value, list)
        if has_min_items and len(value) < int(rules["minItems"]):
            issues.append(
                {"path": str(path), "message": f"line {line_number}: {field} must not be empty"}
            )
    return issues


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    return True
