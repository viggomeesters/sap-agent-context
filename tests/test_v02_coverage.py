from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path

from sap_agent_context.completeness import audit_completeness
from sap_agent_context.model import KnowledgeItem
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]
V02_MATRIX = ROOT / "schema/sap-agent-context-v0.2-coverage.yaml"


def test_v02_coverage_matrix_truthfully_reports_current_fill_gaps() -> None:
    report = audit_completeness(
        load_items(ROOT),
        root=ROOT,
        matrix_path=V02_MATRIX,
        current_date=date(2026, 6, 22),
    )

    areas = {finding["area"] for finding in report["findings"]}
    messages = "\n".join(finding["message"] for finding in report["findings"])

    assert report["status"] == "failed"
    assert report["items"] >= 64
    assert "domain:master_data_material_bp" not in areas
    assert "domain:migration_cockpit" not in areas
    assert "source_traceability" in areas
    assert "sap_role" in messages


def test_v02_coverage_matrix_does_not_pass_with_generic_root_filler() -> None:
    items = load_items(ROOT)
    items_with_generic_filler = items + [
        _generic_root_pointer_item(index) for index in range(1, 90)
    ]

    report = audit_completeness(
        items_with_generic_filler,
        root=ROOT,
        matrix_path=V02_MATRIX,
        current_date=date(2026, 6, 22),
    )

    areas = {finding["area"] for finding in report["findings"]}
    messages = "\n".join(finding["message"] for finding in report["findings"])

    assert len(items_with_generic_filler) >= 120
    assert report["status"] == "failed"
    assert "source_traceability" in areas
    assert "exact_page" in messages
    assert "Knowledge kind sap_role has fewer" in messages


def _generic_root_pointer_item(index: int) -> KnowledgeItem:
    payload = {
        "id": f"sap.ref.generic-filler-{index:03d}",
        "title": f"Generic SAP filler reference {index:03d}",
        "kind": "external_reference",
        "status": "active",
        "access": "public",
        "requires_login": False,
        "sap_product": ["s4hana_cloud_public"],
        "topics": [
            "master-data",
            "migration",
            "procurement",
            "sales",
            "integration",
            "analytics",
        ],
        "used_for": ["fo.source_traceability"],
        "summary": (
            "Generic root pointer used by a regression test to prove volume "
            "is not coverage."
        ),
        "freshness": {
            "valid_from": "2026-06-22",
            "review_after": "2026-12-22",
            "expires_at": "2027-06-22",
            "retrieved_at": "2026-06-22",
        },
        "source": {
            "kind": "public_url",
            "title": "SAP Help Portal root",
            "url": "https://help.sap.com/docs/SAP_S4HANA_CLOUD?locale=en-US",
            "specificity": "exact_page",
            "retrieved_at": "2026-06-22",
            "license_note": "Public SAP URL pointer only; no copied SAP documentation.",
        },
        "claims": [
            {
                "statement": (
                    "This generic root pointer should never satisfy detailed v0.2 "
                    "field, table, or migration cockpit coverage requirements."
                ),
                "evidence": ["https://help.sap.com/docs/SAP_S4HANA_CLOUD"],
            }
        ],
    }
    return KnowledgeItem(path=ROOT / "tests/generated-generic-filler.yaml", data=deepcopy(payload))
