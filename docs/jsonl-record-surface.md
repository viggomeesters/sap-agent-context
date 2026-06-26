# JSONL record surface

SAP Agent Context follows the JSONL-vault-spike principle where it matters for
agent use: **records-first**, source-backed, generated runtime views, and no
hidden mutation. It is not a pure JSONL-primary vault yet; it is a stricter
migration layer from curated YAML into typed agent records.

## Current contract

```text
YAML knowledge files
  -> typed records/*.jsonl
  -> build/context.sqlite + FTS5 + vector corpus + embeddings
  -> bounded context bundles and downstream consumers
```

- **YAML remains the temporary editing source** until the JSONL record surface is
  explicitly promoted as the only edit surface.
- **records/*.jsonl is the deterministic agent-first record surface** for apps,
  tables, fields, workflows, roles, claims, sources, and relations.
- **build/ is generated runtime output**. It is rebuildable, ignored by Git, and
  must not become the source of truth.
- Runtime SQLite, FTS5, vector JSONL, and sqlite-vec rows are projections from
  records, not hand-edited state.

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

## Intentional deviations

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
   YAML source is still active.
3. The consumer contract still exposes `bundle_kind: sap_fo_context_bundle` for
   backward compatibility.

These deviations are allowed only while they are documented here and protected
by the quality gate.

## Future migration path

If/when the repo promotes JSONL as the primary edit surface, migrate in this
order:

1. Add `record_type` to every exported record.
2. Rename item subtype semantics from `kind` to `sap_context_type` while keeping
   `kind` as a deprecated compatibility alias.
3. Add a generated or canonical `items.jsonl` projection containing all item
   records with `record_type: item`.
4. Move downstream consumers from `kind` to `sap_context_type`.
5. Only then remove `kind` from public examples and schemas.

Until that migration is planned and tested, do not do a broad schema rename. The
current goal is a public-safe, source-backed SAP agent context layer, not format
purity at the cost of consumer stability.
