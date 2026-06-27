"""Command line interface for SAP Agent Context."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sap_agent_context.agent_records import export_agent_records, validate_agent_records
from sap_agent_context.bundle import build_context_bundle, mccoy_provider_manifest
from sap_agent_context.completeness import audit_completeness
from sap_agent_context.domain_density import (
    build_domain_density_heatmap,
    render_heatmap_markdown,
    write_heatmap,
)
from sap_agent_context.evaluation import evaluate_fo_output_fixtures
from sap_agent_context.index import build_indexes
from sap_agent_context.repository import load_items
from sap_agent_context.runtime_embeddings import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    build_runtime_embeddings,
    embed_query,
)
from sap_agent_context.runtime_evaluation import evaluate_runtime_retrieval
from sap_agent_context.runtime_search import search_runtime_index
from sap_agent_context.semantic_model_evaluation import evaluate_semantic_models
from sap_agent_context.validation import has_errors, validate_items

DEFAULT_SQLITE = "build/context.sqlite"
DEFAULT_ITEMS_JSONL = "build/items.jsonl"
DEFAULT_VECTOR_JSONL = "build/vector-corpus.jsonl"
DEFAULT_RECORDS_DIR = "records"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sap-agent-context")
    parser.add_argument("--root", type=Path, default=Path("."))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    audit = subparsers.add_parser("audit-completeness")
    audit.add_argument("--matrix", type=Path)

    heatmap = subparsers.add_parser("domain-density-heatmap")
    heatmap.add_argument("--output", type=Path)
    heatmap.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="render as JSON for machines or Markdown for docs/review",
    )

    evaluate = subparsers.add_parser("evaluate-fixtures")
    evaluate.add_argument("--fixtures", type=Path)

    runtime_eval = subparsers.add_parser("evaluate-runtime-retrieval")
    runtime_eval.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    runtime_eval.add_argument("--fixtures", type=Path)

    semantic_eval = subparsers.add_parser("evaluate-semantic-models")
    semantic_eval.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    semantic_eval.add_argument("--items-jsonl", type=Path, default=Path(DEFAULT_ITEMS_JSONL))
    semantic_eval.add_argument("--vector-jsonl", type=Path, default=Path(DEFAULT_VECTOR_JSONL))
    semantic_eval.add_argument("--fixtures", type=Path)
    semantic_eval.add_argument("--provider", default=DEFAULT_EMBEDDING_PROVIDER)
    semantic_eval.add_argument("--models", nargs="+", default=[DEFAULT_EMBEDDING_MODEL])
    semantic_eval.add_argument("--dimension", type=int, default=DEFAULT_EMBEDDING_DIMENSION)
    semantic_eval.add_argument("--batch-size", type=int, default=64)

    build_index = subparsers.add_parser("build-index")
    build_index.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    build_index.add_argument("--items-jsonl", type=Path, default=Path(DEFAULT_ITEMS_JSONL))
    build_index.add_argument("--vector-jsonl", type=Path, default=Path(DEFAULT_VECTOR_JSONL))
    build_index.add_argument(
        "--sqlite-vec",
        choices=["off", "auto", "required"],
        default="auto",
        help="optional sqlite-vec integration mode for generated vector tables",
    )

    build_embeddings = subparsers.add_parser("build-embeddings")
    build_embeddings.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    build_embeddings.add_argument("--vector-jsonl", type=Path, default=Path(DEFAULT_VECTOR_JSONL))
    build_embeddings.add_argument("--provider", default=DEFAULT_EMBEDDING_PROVIDER)
    build_embeddings.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL)
    build_embeddings.add_argument("--dimension", type=int, default=DEFAULT_EMBEDDING_DIMENSION)
    build_embeddings.add_argument("--batch-size", type=int, default=64)

    export_jsonl = subparsers.add_parser("export-jsonl")
    export_jsonl.add_argument("--output-dir", type=Path, default=Path(DEFAULT_RECORDS_DIR))
    export_jsonl.add_argument(
        "--skip-schema-validation",
        action="store_true",
        help="write records without validating them against schema/*.schema.json",
    )

    query = subparsers.add_parser("query")
    query.add_argument("--intent", required=True)
    query.add_argument("--topic", required=True)
    query.add_argument("--sap-product", default="")
    query.add_argument("--limit", type=int, default=8)
    query.add_argument("--output", type=Path)

    runtime_search = subparsers.add_parser("runtime-search")
    runtime_search.add_argument("query")
    runtime_search.add_argument("--sqlite", type=Path, default=Path(DEFAULT_SQLITE))
    runtime_search.add_argument("--limit", type=int, default=12)
    runtime_search.add_argument("--kind", default=None)
    runtime_search.add_argument("--sap-product", default=None)
    runtime_search.add_argument("--access", default=None)
    runtime_search.add_argument("--used-for", default=None)
    runtime_search.add_argument("--topic", default=None)
    runtime_search.add_argument("--vector", action="store_true")
    runtime_search.add_argument("--embedding-provider", default=DEFAULT_EMBEDDING_PROVIDER)
    runtime_search.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    runtime_search.add_argument("--output", type=Path)

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
            sqlite_vec=args.sqlite_vec,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "build-embeddings":
        payload = build_runtime_embeddings(
            sqlite_path=_resolve_output(root, args.sqlite),
            vector_jsonl_path=_resolve_output(root, args.vector_jsonl),
            provider=args.provider,
            model=args.model,
            dimension=args.dimension,
            batch_size=args.batch_size,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "export-jsonl":
        items = load_items(root)
        issues = validate_items(items)
        if has_errors(issues):
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "validation errors block JSONL export",
                        "issues": [issue.to_dict() for issue in issues],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1
        output_dir = _resolve_output(root, args.output_dir)
        payload = export_agent_records(items, output_dir, root=root)
        if not args.skip_schema_validation:
            payload["schema_validation"] = validate_agent_records(
                output_dir, schema_dir=root / "schema"
            )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        schema_validation = payload.get("schema_validation", {"status": "passed"})
        return 0 if schema_validation["status"] == "passed" else 1

    if args.command == "audit-completeness":
        items = load_items(root)
        payload = audit_completeness(
            items,
            root=root,
            matrix_path=_resolve_output(root, args.matrix) if args.matrix else None,
        )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if payload["status"] == "passed" else 1

    if args.command == "domain-density-heatmap":
        items = load_items(root)
        payload = build_domain_density_heatmap(items)
        if args.output:
            write_heatmap(payload, _resolve_output(root, args.output), args.format)
        if args.format == "markdown":
            print(render_heatmap_markdown(payload), end="")
        else:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0

    if args.command == "evaluate-fixtures":
        items = load_items(root)
        payload = evaluate_fo_output_fixtures(
            items,
            root=root,
            fixtures_path=_resolve_output(root, args.fixtures) if args.fixtures else None,
        )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if payload["status"] == "passed" else 1

    if args.command == "evaluate-runtime-retrieval":
        payload = evaluate_runtime_retrieval(
            root=root,
            sqlite_path=_resolve_output(root, args.sqlite),
            fixtures_path=_resolve_output(root, args.fixtures) if args.fixtures else None,
        )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if payload["status"] == "passed" else 1

    if args.command == "evaluate-semantic-models":
        payload = evaluate_semantic_models(
            root=root,
            sqlite_path=_resolve_output(root, args.sqlite),
            items_jsonl_path=_resolve_output(root, args.items_jsonl),
            vector_jsonl_path=_resolve_output(root, args.vector_jsonl),
            fixtures_path=_resolve_output(root, args.fixtures) if args.fixtures else None,
            provider=args.provider,
            models=args.models,
            dimension=args.dimension,
            batch_size=args.batch_size,
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

    if args.command == "runtime-search":
        sqlite_path = _resolve_output(root, args.sqlite)
        query_vector = None
        if args.vector:
            query_vector = embed_query(
                args.query,
                provider=args.embedding_provider,
                model=args.embedding_model,
            )
        results = search_runtime_index(
            sqlite_path,
            args.query,
            limit=args.limit,
            kind=args.kind,
            sap_product=args.sap_product,
            access=args.access,
            used_for=args.used_for,
            topic=args.topic,
            query_vector=query_vector,
        )
        payload = {
            "status": "passed" if results else "empty",
            "query": args.query,
            "sqlite": str(sqlite_path),
            "filters": {
                "kind": args.kind,
                "sap_product": args.sap_product,
                "access": args.access,
                "used_for": args.used_for,
                "topic": args.topic,
            },
            "results": results,
        }
        if args.output:
            output = _resolve_output(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if results else 2

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
