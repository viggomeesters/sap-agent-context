from __future__ import annotations

from sap_agent_context import bundle


def test_bundle_token_helpers_cache_repeated_string_work() -> None:
    bundle._tokens.cache_clear()
    bundle._precision_tokens.cache_clear()

    assert "authorization" in bundle._tokens("SAP authorization authorization")
    assert "authorization" in bundle._tokens("SAP authorization authorization")
    assert bundle._tokens.cache_info().hits >= 1

    assert "authorization" in bundle._precision_tokens("SAP authorization authorization")
    assert "authorization" in bundle._precision_tokens("SAP authorization authorization")
    assert bundle._precision_tokens.cache_info().hits >= 1
