# SAP Agent Context Merge Boundary

This document records the execution boundary for merging the current SAP FO
Knowledge Base direction into one agent-first repository named
`sap-agent-context`.

## Decision

Use one public repository as the default target:

```text
sap-agent-context
```

The repository should be the cloneable SAP context layer for AI agents and human
reviewers. It should contain source-backed, compact context artifacts that help
agents generate or review functional design, field mapping, workflow, role,
scope item, and implementation-support output.

Split into a second private repository only when a candidate source contains
customer data, private screenshots, proprietary implementation evidence, copied
SAP content, or material that cannot be made public with clear provenance.

## Why One Repository

- The current repository already behaves like an agent context provider: YAML
  knowledge items, source pointers, freshness metadata, quality gates, context
  bundle generation, and provider manifests.
- The intended user journey is local clone first: a colleague should be able to
  clone one repository and point their AI tools at a shared SAP context layer.
- Field/object context and functional design context are coupled at retrieval
  time. Splitting them would create duplicate validation, duplicate release
  hygiene, and unclear ownership unless a privacy boundary forces the split.
- The name `sap-agent-context` is narrower and safer than
  `sap-knowledge-base`: it does not claim to contain all SAP knowledge.

## Current Source Evidence

| Source | Status | Use |
| --- | --- | --- |
| `/Users/viggomeesters/Dev/sap-fo-knowledge-base` | Canonical current repository | Starting point for `sap-agent-context`. |
| `/Users/viggomeesters/Dev/sap-field-atlas` | Not found locally during this audit | Do not invent this as a source. If it appears later, audit it before import. |
| `/Users/viggomeesters/Dev/alteryx-flow-agent-toolkit/1-dictionary` | Candidate dictionary source | Contains dictionary docs plus `data-migration-dictionary.xlsx` and `object-registry.xlsx`; review before import. |
| `/Users/viggomeesters/Dev/alteryx-template-flows/1-dictionary` | Candidate dictionary source | Contains dictionary docs plus a smaller `data-migration-dictionary.xlsx`; review before import. |

Observed workbook metadata:

- `alteryx-flow-agent-toolkit/1-dictionary/data-migration-dictionary.xlsx`:
  one sheet, 15,819 rows, 17 columns.
- `alteryx-flow-agent-toolkit/1-dictionary/object-registry.xlsx`: one sheet,
  299 rows, 21 columns.
- `alteryx-template-flows/1-dictionary/data-migration-dictionary.xlsx`: one
  sheet, 5,441 rows, 10 columns.

These workbooks are not imported by this task. They are candidate sources only.

## Canonical In-Scope Domains

The merged repository may contain these public-safe context domains:

- `source-registry`: source pointers, access labels, freshness metadata, and
  review dates.
- `fields`: SAP technical field identity, labels, descriptions, structure-field
  keys, and field-level usage notes.
- `objects`: SAP object and migration object identity, object metadata, and
  object-to-field relationships.
- `field-maps`: mapping patterns, defaulting rules, transformation methods, and
  traceable field mapping guidance.
- `workflows`: approval and business workflow patterns.
- `roles`: generic SAP business roles and authorization context.
- `scope-items`: SAP scope item references and generic implementation scope
  context.
- `functional-design-patterns`: reusable FO sections, test scenarios, decision
  rules, and implementation notes.
- `agent-bundles`: generated context bundles and provider manifests, usually
  under `build/` or another generated-output path.

## Out Of Scope

Do not migrate or publish:

- customer names, tenant data, exports, screenshots, tickets, meeting notes, or
  project-specific implementation evidence;
- copied SAP Help pages, SAP Notes, Learning Hub, SAP for Me material, or other
  proprietary SAP text;
- credentials, `.env` files, access tokens, private keys, cookies, or local
  machine secrets;
- generated binaries or large workbook outputs unless they are deliberately
  reviewed and needed for public examples;
- field atlas or dictionary rows whose source, license, privacy status, or
  business ownership is unclear.

## Stop Criteria

Stop the merge and keep separate public/private repositories if:

- the field atlas source is mostly client-specific or private;
- source licensing does not permit public redistribution of field/object data;
- the import would require copying protected SAP content instead of storing
  compact metadata and source pointers;
- downstream agents require incompatible schemas that cannot be bridged with a
  stable compatibility layer.

## Next Tasks

1. Rebrand public identity from SAP FO Knowledge Base to SAP Agent Context.
2. Define the canonical folder and schema structure for fields, objects,
   workflows, roles, scope items, field maps, source registry, and functional
   design patterns.
3. Import or map candidate field/object material only after provenance and
   privacy review.
4. Update agent and McCoy consumer contracts to use `sap-agent-context` as the
   public provenance and local clone target.
5. Run public-readiness hardening after the merge.
