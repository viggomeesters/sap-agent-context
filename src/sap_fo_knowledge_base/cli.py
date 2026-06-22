"""Command line interface for the SAP FO knowledge base."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sap_fo_knowledge_base.bundle import build_context_bundle, mccoy_provider_manifest
from sap_fo_knowledge_base.completeness import audit_completeness
from sap_fo_knowledge_base.index import build_indexes
from sap_fo_knowledge_base.repository import load_items
from sap_fo_knowledge_base.validation import has_errors, validate_items

DEFAULT_SQLITE = "build/kb.sqlite"
DEFAULT_ITEMS_JSONL = "build/items.jsonl"
DEFAULT_VECTOR_JSONL = "build/vector-corpus.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sap-fo-kb")
    parser.add_argument("--root", type=Path, default=Path("."))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    audit = subparsers.add_parser("audit-completeness")
    audit.add_argument("--matrix", type=Path)

    build_index = subparsers.add_parser("build-index")
    build_index.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    build_index.add_argument("--items-jsonl", type=Path, default=Path(DEFAULT_ITEMS_JSONL))
    build_index.add_argument("--vector-jsonl", type=Path, default=Path(DEFAULT_VECTOR_JSONL))

    query = subparsers.add_parser("query")
    query.add_argument("--intent", required=True)
    query.add_argument("--topic", required=True)
    query.add_argument("--sap-product", default="")
    query.add_argument("--limit", type=int, default=8)
    query.add_argument("--output", type=Path)

    provider = subparsers.add_parser("mccoy-provider")
    provider.add_argument("bundle", type=Path)
    provider.add_argument("--title", default="")
    provider.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if args.command == "validate":
        items = load_items(root)
        issues = validate_items(items)
        payload = {
            "status": "failed" if has_errors(issues) else "passed",
            "items": len(items),
            "issues": [issue.to_dict() for issue in issues],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if has_errors(issues) else 0

    if args.command == "build-index":
        items = load_items(root)
        issues = validate_items(items)
        if has_errors(issues):
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "validation errors block index build",
                        "issues": [issue.to_dict() for issue in issues],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1
        payload = build_indexes(
            items,
            sqlite_path=_resolve_output(root, args.sqlite),
            jsonl_path=_resolve_output(root, args.items_jsonl),
            vector_jsonl_path=_resolve_output(root, args.vector_jsonl),
            root=root,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "audit-completeness":
        items = load_items(root)
        payload = audit_completeness(
            items,
            root=root,
            matrix_path=_resolve_output(root, args.matrix) if args.matrix else None,
        )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if payload["status"] == "passed" else 1

    if args.command == "query":
        items = load_items(root)
        issues = validate_items(items)
        if has_errors(issues):
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "validation errors block bundle generation",
                        "issues": [issue.to_dict() for issue in issues],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1
        bundle = build_context_bundle(
            items,
            root=root,
            intent=args.intent,
            topic=args.topic,
            sap_product=args.sap_product,
            limit=args.limit,
        )
        if args.output:
            output = _resolve_output(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(bundle, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(bundle, indent=2, sort_keys=True, default=str))
        return 0 if bundle["status"] == "ready" else 2

    if args.command == "mccoy-provider":
        bundle_path = _resolve_output(root, args.bundle)
        payload = mccoy_provider_manifest(
            bundle_path,
            title=args.title or None,
        )
        if args.output:
            output = _resolve_output(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


def _resolve_output(root: Path, output: Path) -> Path:
    return output if output.is_absolute() else root / output


if __name__ == "__main__":
    raise SystemExit(main())
