# JSONL migration boundary

SAP Agent Context is in a JSONL-native migration. This page defines what agents may edit directly and what must stay generated or compatibility-only.

## Canonical state

`records/*.jsonl` is the canonical agent-facing record surface for typed context records:

- apps, tables, fields, workflows and roles as item records;
- claims that make reusable assertions explicit;
- sources that carry access, freshness and citation metadata;
- relations that connect items without relying on prose-only inference.

The supported direct authoring smoke path is:

```bash
uv run sap-agent-context validate-records --records-dir records
```

Use it before treating a JSONL authoring change as loadable. Errors must be fixed at the record path and id reported by the command.

## Compatibility state

YAML under `knowledge/**/*.yaml` is a legacy authoring/import format. It may still be edited for bounded maintainer-curated packs while the migration is active, but it is not the runtime or consumer source of truth.

Allowed compatibility flow:

```text
knowledge/**/*.yaml
  -> uv run sap-agent-context export-jsonl --output-dir records
  -> records/*.jsonl
  -> build/context.sqlite + build/vector-corpus.jsonl
  -> bundles and retrieval evaluations
```

If YAML and JSONL disagree, repair the import/export or the specific authoring record. Do not declare YAML authoritative again to make a failing gate pass.

## Generated state

These artifacts are generated read models, not authoring targets:

- `build/context.sqlite`
- `build/items.jsonl`
- `build/vector-corpus.jsonl`
- vector embedding rows and metadata
- generated context bundles under `build/context-bundles/`

Rebuild them from records. Do not hand-edit them to fix retrieval, bundle, freshness, source, or evaluation failures.

## Migration guardrails for agents

Do:

1. Make bounded, source-labelled changes.
2. Validate records with `validate-records` and run the normal quality gate.
3. Keep `kind` until consumers are migrated to `record_type` and `sap_context_type`.
4. Preserve `source_ids`, `claim_ids`, `relation_ids`, `subject_id`, `target_id`, and freshness metadata.
5. Keep public/gated/internal access labels explicit.

Do not:

1. Bulk import broad SAP content to inflate item counts.
2. Mass-rename `kind` or split/merge record files without a consumer migration task.
3. Edit generated `build/` artifacts directly.
4. Add customer/client data, SAP system screenshots, tenant URLs, SAP Notes text, credentials, tickets, or internal project identifiers.
5. Weaken evaluation or completeness gates when stale, gated, expired, or ambiguous evidence should fail closed.

## Current migration boundary

The current stable boundary is JSONL-first with legacy YAML import. A fully JSONL-native authoring model is not complete until direct authoring tools, downstream consumers, and retrieval fixtures all pass with additive `record_type` / `sap_context_type` semantics.

Until then, prefer small record-safe slices over repo-wide conversion. A green migration slice proves one bounded behavior and keeps generated artifacts reproducible from `records/*.jsonl`.
