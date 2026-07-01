# JSONL record surface

SAP Agent Context is **JSONL-first** and records-first: `records/*.jsonl` is the
canonical agent record surface. YAML still exists in the repository only as a
legacy authoring/import format while older curation workflows are being
migrated.

## Current contract

```text
legacy YAML authoring/import files
  -> records/*.jsonl
  -> build/context.sqlite + FTS5 + vector corpus + embeddings
  -> bounded context bundles and downstream consumers
```

In source-of-truth terms:

```text
JSONL -> build/context.sqlite
```

- **records/*.jsonl is the canonical agent record surface** for apps, tables,
  fields, workflows, roles, claims, sources, and relations.
- **YAML is a legacy authoring/import format**, not the source of truth. It may
  remain temporarily because existing pack-level authoring and some tests still
  inspect legacy files directly.
- **build/ is generated runtime output**. It is rebuildable, ignored by Git, and
  must not become authoritative.
- Runtime SQLite, FTS5, vector JSONL, and sqlite-vec rows are projections from
  records, not hand-edited state.
- Do not add new YAML-first source-of-truth language. New docs and gates must
  describe YAML as legacy import/authoring only.

## Why YAML still exists

YAML remains as a legacy pack-level authoring/import convenience while the repo
finishes migrating to records-first workflows. That is an implementation
convenience, not a truth boundary. The durable agent-facing contract is the
exported JSONL record surface and the generated runtime indexes derived from it.

Practically:

- bounded maintainer curation may still touch `knowledge/**/*.yaml` during the
  migration;
- `export-jsonl` synchronizes those legacy authoring files into records;
- build/runtime/evidence contracts must treat `records/*.jsonl` as canonical;
- if YAML and JSONL diverge, the fix is to resync records or migrate the authoring
  path, not to call YAML authoritative again.

## Alignment with JSONL-vault-spike

SAP Agent Context keeps the useful JSONL-vault-spike philosophy:

- Do not model one YAML file or Markdown note as one JSONL line.
- Extract knowledge units: items, claims, sources, relations, freshness,
  retrieval hints, and bundle/eval expectations.
- Keep primary IDs stable and reference-like fields explicit:
  `source_ids`, `claim_ids`, `relation_ids`, `subject_id`, `target_id`, and
  `evidence_ids`.
- Treat generated SQLite, vectors, and bundles as rebuildable read models.
- Keep public data source-labelled and access-labelled; customer evidence stays
  outside this public repo.

## Intentional deviations / compatibility deviations

The latest JSONL-vault-spike naming preference is:

```json
{"record_type":"item","sap_context_type":"sap_app"}
```

This repo currently uses a compatibility shape:

```json
{"kind":"sap_app"}
```

That is intentional for now:

1. `kind` is a compatibility field used by existing bundle contracts, tests, and
   downstream consumers.
2. Item records are split by domain file (`apps.jsonl`, `tables.jsonl`,
   `fields.jsonl`, `workflows.jsonl`, `roles.jsonl`) for reviewability while the
   legacy YAML authoring path is still active.
3. The consumer contract still exposes `bundle_kind: sap_fo_context_bundle` for
   backward compatibility.

These deviations are allowed only while they are documented here and protected
by the quality gate.

## Future migration path

To remove the legacy YAML authoring path entirely, migrate in this order:

1. Add `record_type` to every exported record.
2. Rename item subtype semantics from `kind` to `sap_context_type` while keeping
   `kind` as a deprecated compatibility alias.
3. Add a canonical `items.jsonl` projection containing all item records with
   `record_type: item`.
4. Move downstream consumers from `kind` to `sap_context_type`.
5. Move authoring tools to write JSONL records directly.
6. Only then delete or archive legacy YAML authoring files.

Until that migration is planned and tested, do not do a broad schema rename or
mass file-format conversion. The current fix is to make the truth boundary
honest: JSONL first, YAML legacy import only.
