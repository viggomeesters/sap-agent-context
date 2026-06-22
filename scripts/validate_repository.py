#!/usr/bin/env python3
"""Validate public repository identity and obvious private-data hazards."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "__pycache__",
}
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".svg",
    ".gitignore",
}
EXTRA_TEXT_FILES = {"Makefile", "AGENTS.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md"}
BLOCKED_STRINGS = {
    "sap_fo_knowledge_base": "old Python module slug",
    "sap-fo-knowledge-base": "old package/repository slug",
    "sap-fo-kb": "old CLI alias",
    "sap-fo-context-bundle.schema": "old schema filename",
}
SECRET_MARKERS = {
    "BEGIN PRIVATE KEY": "private key material",
    "AWS_SECRET_ACCESS_KEY": "AWS secret marker",
    "SAP_PASSWORD": "SAP password marker",
    "CLIENT_SECRET": "generic client secret marker",
    "TENANT_EXPORT": "tenant export marker",
}


def main() -> int:
    failures: list[str] = []
    for path in iter_text_files(ROOT):
        if path == Path(__file__).resolve():
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for needle, reason in BLOCKED_STRINGS.items():
            if needle in text:
                failures.append(f"{rel}: blocked {reason}: {needle}")
        for needle, reason in SECRET_MARKERS.items():
            if needle in text:
                failures.append(f"{rel}: possible {reason}: {needle}")

    if not (ROOT / "src" / "sap_agent_context").is_dir():
        failures.append("src/sap_agent_context missing")
    if not (ROOT / "schema" / "sap-agent-context-bundle.schema.yaml").is_file():
        failures.append("schema/sap-agent-context-bundle.schema.yaml missing")

    if failures:
        print("repository guard failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("repository guard passed")
    return 0


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in EXTRA_TEXT_FILES:
            yield path


if __name__ == "__main__":
    raise SystemExit(main())
