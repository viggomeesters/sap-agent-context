from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_real_public_clone_url_and_no_placeholder() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "git clone https://github.com/viggomeesters/sap-agent-context.git" in readme
    assert "<repo-url>" not in readme
    assert "bundle_kind: sap_fo_context_bundle" in readme


def test_public_readiness_documents_release_and_privacy_boundaries() -> None:
    doc = (ROOT / "docs/public-readiness.md").read_text(encoding="utf-8")

    required = [
        "https://github.com/viggomeesters/sap-agent-context.git",
        "make check",
        "Releases are explicit-only",
        "credentials, `.env` files, API keys, private keys, and tokens",
        "customer-specific SAP tenant data",
        "bundle_kind: sap_fo_context_bundle",
        "generic executive dashboard performance report",
    ]
    for text in required:
        assert text in doc

    assert "No GitHub remote is configured" not in doc
    assert "git remote add origin <repo-url>" not in doc


def test_clone_first_examples_cover_ready_and_fail_closed_queries() -> None:
    example = (ROOT / "examples/clone-first-queries.md").read_text(encoding="utf-8")

    assert "make check" in example
    assert example.count("uv run sap-agent-context query") >= 5
    assert "Expected: `status: ready`" in example
    assert "Expected: `status: needs_curation`" in example
    assert "generic executive dashboard performance report" in example
