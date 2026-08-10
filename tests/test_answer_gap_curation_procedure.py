from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "docs" / "answer-gap-curation-procedure.json"


def test_answer_gap_curation_procedure_is_machine_readable_and_mandatory() -> None:
    payload = json.loads(PROCEDURE.read_text(encoding="utf-8"))

    assert payload["schema"] == "sap-agent-context.answer-gap-curation-procedure.v1"
    assert payload["artifact_kind"] == "answer_gap_curation_procedure"
    assert "Do not stop at the gap" in payload["trigger"]["mandatory_action"]
    assert [step["name"] for step in payload["procedure"]] == [
        "probe_local_context",
        "research_sources",
        "curate_answer_contract",
        "bind_ready_answer",
        "regenerate",
        "verify",
        "answer_user",
    ]
    required = set(payload["required_curation_fields"])
    assert {"exact_question", "answer_claim", "source_url_or_gated_pointer"} <= required
    assert "The exact question returns status ready from consultant-answer." in payload["done_when"]


def test_agents_contract_routes_needs_curation_into_procedure() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Mandatory answer-gap curation" in agents
    assert "docs/answer-gap-curation-procedure.json" in agents
    assert "do not stop at the gap" in agents
