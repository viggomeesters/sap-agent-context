from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "consumer-contract-json-examples.json"
SCHEMA = ROOT / "schema" / "consumer-contract-json-examples.schema.json"
OLD_EXAMPLES = ROOT / "examples" / "consumer-contract-json-examples.md"

REQUIRED_SURFACES = {
    "context_bundle",
    "query_explain",
    "consultant_answer",
    "answer_profile",
}


def _payload() -> dict:
    return json.loads(EXAMPLES.read_text(encoding="utf-8"))


def test_consumer_contract_json_examples_are_schema_backed_json() -> None:
    payload = _payload()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert payload["schema"] == "sap-agent-context.consumer-contract-json-examples.v1"
    assert payload["artifact_kind"] == "consumer_contract_json_examples"
    assert schema["$id"].endswith("/consumer-contract-json-examples.schema.json")
    assert len(payload["examples"]) >= 4
    assert not OLD_EXAMPLES.exists()


def test_consumer_contract_json_examples_cover_runtime_surfaces() -> None:
    payload = _payload()
    surfaces = {example["source_surface"] for example in payload["examples"]}
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)

    assert surfaces >= REQUIRED_SURFACES
    assert "query-explain" in text
    assert "consultant-answer" in text
    assert "schema/answer-profiles.json" in text
    assert "status=needs_curation" in text
    assert "report_only" in text


def test_consumer_contract_json_examples_preserve_boundaries() -> None:
    text = json.dumps(_payload(), sort_keys=True, ensure_ascii=False).lower()

    required = [
        "tenant_specific_truth=false",
        "live_web_validation=false",
        "expert_certification=false",
        "ready is starter context, not tenant truth",
        "needs_curation is draft-only",
        "do not claim live sap help verification",
        "do not convert ready into tenant-specific configuration proof",
        "citations",
        "source ids",
        "freshness",
    ]
    for phrase in required:
        assert phrase in text

    forbidden = ["password", "client secret", "customer tenant", "anne", "mcCoy customer"]
    for phrase in forbidden:
        assert phrase.lower() not in text
