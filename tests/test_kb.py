from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import yaml

from sap_agent_context.bundle import build_context_bundle, mccoy_provider_manifest
from sap_agent_context.completeness import audit_completeness
from sap_agent_context.evaluation import evaluate_fo_output_fixtures
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.validation import has_errors, validate_items

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_items_validate() -> None:
    items = load_items(ROOT)
    issues = validate_items(items, current_date=date(2026, 6, 21))

    assert len(items) >= 50
    assert not has_errors(issues), [issue.to_dict() for issue in issues]


def test_build_indexes_writes_sqlite_jsonl_and_vector_ready_chunks(tmp_path: Path) -> None:
    items = load_items(ROOT)
    report = build_indexes(
        items,
        sqlite_path=tmp_path / "kb.sqlite",
        jsonl_path=tmp_path / "items.jsonl",
        vector_jsonl_path=tmp_path / "vector-corpus.jsonl",
        root=ROOT,
    )

    assert report["items"] == len(items)
    with sqlite3.connect(tmp_path / "kb.sqlite") as conn:
        row = conn.execute(
            "SELECT title, expires_at FROM items WHERE id = ?",
            ("sap.app.manage-workflows-supplier-invoices",),
        ).fetchone()
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
        tables = {row[0] for row in table_rows}
        counts = dict(
            conn.execute(
                """
                SELECT 'items', count(*) FROM items
                UNION ALL SELECT 'claims', count(*) FROM claims
                UNION ALL SELECT 'sources', count(*) FROM sources
                UNION ALL SELECT 'relations', count(*) FROM relations
                """
            ).fetchall()
        )
        claim_payload = conn.execute(
            "SELECT payload_json FROM claims WHERE subject_id = ? LIMIT 1",
            ("sap.app.eam.pm.ie03",),
        ).fetchone()
        source_payload = conn.execute(
            "SELECT payload_json FROM sources WHERE subject_id = ? LIMIT 1",
            ("sap.app.eam.pm.ie03",),
        ).fetchone()
    assert row == ("Manage Workflows for Supplier Invoices", "2026-12-21")
    assert {"items", "claims", "sources", "relations", "item_topics", "item_used_for"} <= tables
    assert counts["items"] == len(items)
    assert counts["claims"] > counts["items"]
    assert counts["sources"] == len(items)
    assert counts["relations"] > 0
    assert json.loads(claim_payload[0])["subject_id"] == "sap.app.eam.pm.ie03"
    assert json.loads(source_payload[0])["subject_id"] == "sap.app.eam.pm.ie03"

    item_lines = (tmp_path / "items.jsonl").read_text(encoding="utf-8").splitlines()
    vector_lines = (tmp_path / "vector-corpus.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(item_lines) == len(items)
    assert len(vector_lines) > len(items)
    assert json.loads(vector_lines[0])["text"]
    assert any(json.loads(line)["id"].endswith("#statement") for line in vector_lines)


def test_context_bundle_selects_supplier_invoice_workflow_items() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.workflow",
        topic="supplier-invoice workflow",
        sap_product="s4hana_cloud_public",
        limit=12,
        current_date=date(2026, 6, 21),
    )

    ids = {item["id"] for item in bundle["items"]}
    assert bundle["status"] == "ready"
    assert bundle["producer"]["name"] == "sap-agent-context"
    assert bundle["producer"]["contract"] == "sap-agent-context-bundle"
    assert bundle["bundle_kind"] == "sap_fo_context_bundle"
    assert "sap.app.manage-workflows-supplier-invoices" in ids
    assert "sap.field-set.supplier-invoice-routing" in ids
    assert "sap.test-pattern.supplier-invoice-workflow" in ids
    assert bundle["citations"]
    assert bundle["quality_signals"]["gap_count"] == 0
    assert "sap_field" in bundle["quality_signals"]["item_kind_counts"]
    assert "sap_app" in bundle["quality_signals"]["item_kind_counts"]
    assert bundle["quality_signals"]["expired_count"] == 0
    assert all("expires_at" in item and item["expired"] is False for item in bundle["items"])
    assert bundle["mccoy_integration"]["register_as"] == "local_folder"


def test_context_layout_documents_field_atlas_merge_shape() -> None:
    layout = yaml.safe_load((ROOT / "schema/context-layout.yaml").read_text())

    assert layout["canonical_folders"]["fields"]["path"] == "knowledge/fields"
    assert "sap_field" in layout["canonical_folders"]["fields"]["item_kinds"]
    assert "knowledge/sap-objects" in layout["canonical_folders"]["objects"]["legacy_aliases"]
    assert (
        layout["import_policy"]["field_atlas_sources"]
        == "archived-public-provenance-source-only"
    )
    assert layout["import_policy"]["field_atlas_contract"] == (
        "schema/field-atlas-absorption-contract.yaml"
    )


def test_completeness_audit_reports_no_critical_or_important_gaps() -> None:
    report = audit_completeness(
        load_items(ROOT),
        root=ROOT,
        current_date=date(2026, 6, 22),
    )

    assert report["status"] == "passed"
    assert report["critical"] == 0
    assert report["important"] == 0
    assert report["items"] >= 50


def test_completeness_audit_checks_representative_query_quality_dimensions(
    tmp_path: Path,
) -> None:
    matrix = yaml.safe_load((ROOT / "schema/completeness-matrix.yaml").read_text())
    matrix["representative_queries"][0]["required_dimensions"] = ["access_policy"]
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix), encoding="utf-8")

    report = audit_completeness(
        load_items(ROOT),
        root=ROOT,
        matrix_path=matrix_path,
        current_date=date(2026, 6, 22),
    )

    assert report["status"] == "failed"
    assert any(
        finding["area"] == "query:workflow_supplier_invoice"
        and "missing quality dimension: access_policy" in finding["message"]
        for finding in report["findings"]
    )


def test_gated_and_access_policy_items_are_loaded() -> None:
    items = load_items(ROOT)

    assert any(item.access == "gated" and item.data["requires_login"] for item in items)
    assert any(item.kind == "access_policy" for item in items)


def test_curated_items_record_source_specificity_and_release_applicability() -> None:
    items = load_items(ROOT)

    items_with_source_specificity = [
        item
        for item in items
        if isinstance(item.data.get("source"), dict) and item.data["source"].get("specificity")
    ]
    items_with_release_applicability = [
        item for item in items if isinstance(item.data.get("release_applicability"), dict)
    ]

    assert len(items_with_source_specificity) >= 3
    assert len(items_with_release_applicability) >= 3


def test_stale_source_is_reported_as_warning() -> None:
    issues = validate_items(load_items(ROOT), current_date=date(2027, 1, 1))

    assert any(
        issue.severity == "warning" and "review_after is stale" in issue.message for issue in issues
    )


def test_expired_source_is_reported_as_warning() -> None:
    issues = validate_items(load_items(ROOT), current_date=date(2028, 1, 1))

    assert any(
        issue.severity == "warning" and "expires_at is expired" in issue.message
        for issue in issues
    )


def test_expired_items_make_bundle_needs_curation() -> None:
    bundle = build_context_bundle(
        load_items(ROOT),
        root=ROOT,
        intent="fo.workflow",
        topic="supplier-invoice workflow",
        sap_product="s4hana_cloud_public",
        limit=12,
        current_date=date(2028, 1, 1),
    )

    assert bundle["status"] == "needs_curation"
    assert bundle["quality_signals"]["expired_count"] > 0
    assert any("past expires_at" in gap for gap in bundle["gaps"])


def test_representative_bundles_have_no_unexpected_gaps() -> None:
    items = load_items(ROOT)
    queries = [
        ("fo.workflow", "supplier-invoice workflow"),
        ("fo.sap_configuration", "procurement purchase requisition workflow"),
        ("fo.field_mapping", "business partner master data"),
        ("fo.test_scenarios", "sales order output management"),
        ("fo.authorization", "integration communication role authorization api"),
    ]

    for intent, topic in queries:
        bundle = build_context_bundle(
            items,
            root=ROOT,
            intent=intent,
            topic=topic,
            sap_product="s4hana_cloud_public",
            limit=12,
            current_date=date(2026, 6, 22),
        )
        assert bundle["status"] == "ready"
        assert bundle["gaps"] == []


def test_fo_output_evaluation_fixtures_pass() -> None:
    report = evaluate_fo_output_fixtures(
        load_items(ROOT),
        root=ROOT,
        current_date=date(2026, 6, 22),
    )

    assert report["status"] == "passed", report["results"]
    assert report["fixtures"] >= 4


def test_context_bundle_contract_schema_is_documented() -> None:
    schema = yaml.safe_load((ROOT / "schema/sap-agent-context-bundle.schema.yaml").read_text())

    assert schema["public_contract_name"] == "sap-agent-context-bundle"
    assert schema["bundle_kind"] == "sap_fo_context_bundle"
    assert "producer" in schema["required_top_level"]
    assert "quality_signals" in schema["required_top_level"]
    assert "citations" in schema["required_top_level"]
    assert "expires_at" in schema["items"]["required_fields"]
    assert "expired" in schema["items"]["required_fields"]


def test_mccoy_provider_manifest_points_to_bundle_folder(tmp_path: Path) -> None:
    bundle_path = tmp_path / "context-bundles" / "supplier-invoice-workflow.json"
    bundle_path.parent.mkdir()
    bundle_path.write_text("{}", encoding="utf-8")

    manifest = mccoy_provider_manifest(
        bundle_path, title="SAP Agent Context bundle - supplier-invoice"
    )

    assert manifest["type"] == "local-folder"
    assert manifest["path"] == str(bundle_path.parent)
    assert manifest["provenance"] == "sap-agent-context"
    assert "fo-gen-v2 register-source" in manifest["mccoy_command"]
    assert "sap-agent-context" in manifest["mccoy_command"]
