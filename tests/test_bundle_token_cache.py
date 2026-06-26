from __future__ import annotations

from sap_agent_context import bundle


def test_bundle_token_helpers_cache_repeated_string_work() -> None:
    bundle._tokens.cache_clear()
    bundle._precision_tokens.cache_clear()

    tokens = bundle._tokens("SAP authorization authorization")
    assert "authorization" in tokens
    assert "authorization" in bundle._tokens("SAP authorization authorization")
    assert not hasattr(tokens, "add")
    assert bundle._tokens.cache_info().hits >= 1

    precision_tokens = bundle._precision_tokens("SAP authorization authorization")
    assert "authorization" in precision_tokens
    assert "authorization" in bundle._precision_tokens("SAP authorization authorization")
    assert not hasattr(precision_tokens, "add")
    assert bundle._precision_tokens.cache_info().hits >= 1
