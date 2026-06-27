# Agent-First Specification

SAP Agent Context should be optimized for agents that retrieve, reason, cite,
validate, and detect gaps. Human readability is useful, but it is not the
primary design center. The repository should behave like a portable context
operating system that any agent can clone, validate, index, and use without a
hosted service or private account.

This document defines the target architecture. The current repository may still
use YAML while it migrates toward this contract.

## Design Goal

The canonical source of truth should be small, typed, stable records that agents
can process deterministically. Runtime databases, vector indexes, hosted
services, and generated bundles should be build outputs, not the canonical
source.

Core principle:

```text
canonical records -> validation -> indexes/databases -> bundles -> agent usage
```

## Canonical Source Of Truth

The target canonical layer is JSON Lines plus JSON Schema:

```text
records/
  apps.jsonl
  tables.jsonl
  fields.jsonl
  workflows.jsonl
  roles.jsonl
  claims.jsonl
  sources.jsonl
  relations.jsonl

schema/
  item.schema.json
  claim.schema.json
  relation.schema.json
  source.schema.json
  bundle.schema.json
  eval.schema.json
```

JSONL is preferred because it is streamable, append-friendly, deterministic,
easy to validate, easy to diff, and directly consumable by Python, Node,
SQLite/libSQL, DuckDB, vector pipelines, and hosted stores.

SQLite, libSQL, Turso, DuckDB, vector files, and context bundles are generated
artifacts. They are important runtime surfaces, but they should not become the
canonical source of truth.

## Record Contract

Every canonical record should be:

- typed;
- addressable by a stable id;
- source-labelled;
- freshness-labelled;
- confidence-labelled;
- relation-aware;
- retrievable by intent and topic;
- safe for public reuse.

Minimum item shape:

```json
{
  "id": "sap.app.eam.pm.ie03",
  "kind": "sap_app",
  "title": "IE03 - Display equipment",
  "summary": "SAP GUI transaction context for displaying equipment master data.",
  "topics": ["sap-gui", "eam", "plant-maintenance", "equipment"],
  "used_for": ["fo.navigation", "fo.test_scenarios"],
  "access": "internal_derived",
  "requires_login": false,
  "freshness": {
    "last_reviewed": "2026-06-24",
    "review_after": "2026-12-24"
  },
  "claims": [
    {
      "statement": "IE03 is used as SAP GUI display context for equipment master data.",
      "confidence": "medium",
      "evidence_ids": ["sap.ref.eam.pm.transaction-code-public-cross-check"]
    }
  ],
  "relations": [
    {
      "type": "operates_on",
      "target_id": "sap.object.eam-equipment"
    }
  ],
  "retrieval": {
    "keywords": ["IE03", "equipment display", "SAP GUI"],
    "queries": [
      "Which SAP GUI transaction displays equipment?",
      "How do I open equipment master data in display mode?"
    ],
    "negative_keywords": ["create equipment", "change equipment"]
  }
}
```

## First-Class Claims

Agents need claim-level evidence, not only item summaries. Claims should be
first-class units whenever possible:

```json
{
  "id": "sap.claim.eam.pm.ie03.displays-equipment",
  "subject_id": "sap.app.eam.pm.ie03",
  "statement": "IE03 is used as SAP GUI display context for equipment master data.",
  "confidence": "medium",
  "evidence_ids": ["sap.ref.eam.pm.transaction-code-public-cross-check"],
  "freshness_id": "sap.freshness.reviewed-2026-06-24",
  "usage_constraints": [
    "Verify transaction availability, screen variants, and authorizations in the target SAP system."
  ]
}
```

This lets agents cite exactly what supports an answer and identify where
evidence is weak, stale, gated, or missing.

## Relations

Relations should be explicit records, not implied by prose. Recommended relation
types include:

- `operates_on`
- `has_field`
- `has_table`
- `used_in_process`
- `requires_role`
- `depends_on`
- `source_for`
- `supersedes`
- `contradicts`
- `compatible_with`

Relations should only point to existing canonical ids and must be validated for
referential integrity.

## Retrieval Contract

Retrieval is part of the data contract. Agents should not have to infer all
search behavior from summaries alone.

Each item may include:

- positive keywords;
- negative keywords;
- representative user/agent queries;
- intended use cases;
- forbidden use cases;
- topic aliases;
- language aliases where useful.

Retrieval fixtures should verify that expected records are selected and
confusing records are excluded.

## Bundle Contract

Bundles are the main product surface for agents. A bundle should be a bounded,
auditable context package for a specific goal.

Expected bundle shape:

```json
{
  "bundle_id": "sap.bundle.eam-equipment-display",
  "goal": "Write functional design context for SAP GUI equipment display.",
  "status": "ready",
  "items": ["sap.app.eam.pm.ie03", "sap.object.eam-equipment"],
  "claims": ["sap.claim.eam.pm.ie03.displays-equipment"],
  "source_references": ["sap.ref.eam.pm.transaction-code-public-cross-check"],
  "warnings": [
    "Verify transaction availability, screen variants, and authorizations in the target SAP system."
  ],
  "gaps": [],
  "confidence": "medium"
}
```

Agents should be able to consume a bundle without scanning the whole repository.
Bundles should include enough metadata to cite sources, explain uncertainty, and
decline unsupported claims.

## Generated Runtime Surfaces

Generated outputs should be deterministic and rebuildable:

```text
build/
  context.sqlite
  items.jsonl
  vector-corpus.jsonl
records/
  apps.jsonl
  tables.jsonl
  fields.jsonl
  workflows.jsonl
  roles.jsonl
  claims.jsonl
  sources.jsonl
  relations.jsonl
```

Current runtime contract:

- `records/*.jsonl` is the canonical agent record surface.
- `build/context.sqlite` is the primary local clone-and-go runtime database.
  It contains item/claim/source/relation tables and FTS5 indexes.
- `build/vector-corpus.jsonl` is the deterministic local embedding input.
- `sqlite-vec` is optional and local-only. `build-index --sqlite-vec auto`
  reports skipped when unavailable; `--sqlite-vec required` fails clearly.
- DuckDB is an optional analytics, audit, coverage, and embedding-quality
  companion. It is not the primary agent runtime store.

No hosted service should be required for the base repository workflow, and cloud
vector dependencies must not be introduced as a default path.

## Evaluation Contract

Agent-first quality depends on deterministic evals. Evals should cover
retrieval, bundle quality, adversarial confusion, evidence integrity, freshness,
and public-data safety.

Example retrieval fixture:

```json
{
  "id": "eam_equipment_display_transaction",
  "query": "Which SAP GUI transaction displays equipment?",
  "expected_item_ids": ["sap.app.eam.pm.ie03"],
  "forbidden_item_ids": ["sap.app.eam.pm.ie01", "sap.app.eam.pm.ie02"],
  "required_warning_contains": ["authorizations"]
}
```

The repository should fail validation when records cannot support expected
agent behavior.

## Public Data Boundary

The public-data boundary remains non-negotiable. Canonical records and generated
artifacts must not contain:

- customer or client names;
- SAP system screenshots or exports;
- internal URLs, tickets, project ids, or proprietary mappings;
- copied proprietary SAP documentation;
- secrets, credentials, cookies, `.env` files, or private keys.

Allowed content remains generic SAP context, public source references,
access-labelled gated pointers, confidence-labelled consultant knowledge, and
synthetic examples without customer data.

## Migration Path

The current YAML knowledge files can migrate incrementally:

1. Keep JSONL record validation and bundle behavior green.
2. Keep legacy YAML authoring/import synchronized into `records/*.jsonl` while migration remains active.
3. Add JSON Schema validation for exported records.
4. Add SQLite/libSQL and DuckDB build targets from JSONL.
5. Move retrieval hints, claims, and relations into stricter record shapes.
6. Promote JSONL to canonical once the generated YAML compatibility path is no
   longer needed.

During migration, the repository should preserve the existing public package,
module, CLI, and bundle identities.

## North Star

SAP Agent Context should help agents do four things reliably:

```text
retrieve
reason
cite
detect gaps
```

The best architecture for that goal is:

```text
JSONL records + JSON Schema + eval fixtures as canonical contract
SQLite/libSQL, DuckDB, Turso, vectors, and bundles as generated outputs
```
