# Context Structure

SAP Agent Context uses one knowledge model for field atlas content and
functional design context. The machine-readable layout contract lives in
`schema/context-layout.yaml`.

## Canonical Folders

| Domain | Canonical path | Item kinds | Notes |
| --- | --- | --- | --- |
| Source registry | `knowledge/source-registry/` | `external_reference` | Link-first public or gated source pointers. |
| Fields | `knowledge/fields/` | `sap_field` | Reviewed field identity, meaning, usage, and verification notes. |
| Objects | `knowledge/objects/` | `sap_object` | Business object anchors. `knowledge/sap-objects/` remains a legacy alias during migration. |
| Apps | `knowledge/apps/` | `sap_app` | SAP app/configuration anchors. `knowledge/sap-apps/` remains a legacy alias during migration. |
| Workflows | `knowledge/workflows/` | `decision_rule` | Workflow and approval decision rules. `knowledge/decision-rules/` remains a legacy alias. |
| Roles | `knowledge/roles/` | `sap_role` | Generic business-role context and tenant verification notes. |
| Scope items | `knowledge/scope-items/` | `scope_item` | SAP scope item anchors. |
| Field maps | `knowledge/field-maps/` | `field_map` | Mapping patterns, defaults, transformations, and owner notes. |
| Functional design patterns | `knowledge/fo-patterns/` | `fo_pattern`, `test_pattern`, `access_policy` | Reusable FO quality patterns and tests. |

Existing `knowledge/sap-objects/`, `knowledge/sap-apps/`, and
`knowledge/decision-rules/` files are valid aliases until they are migrated in a
separate move-only change. The current task does not bulk-move files because the
priority is preserving retrieval, validation, and fixture behavior.

## Field Atlas Policy

Field atlas material may be imported only after source review. Review-pending Excel
sources in sibling repositories are not canonical until each row or derived item
has:

- a public-safe source/provenance note;
- no customer names, tenant data, screenshots, or proprietary implementation
  evidence;
- no copied SAP Help, SAP Notes, Learning Hub, or SAP for Me content;
- a stable `sap.field` or `sap.field-set` item id;
- a relation to the relevant object, field map, workflow, or FO pattern.

## Naming Rules

- Use `sap.field-set.<domain>` for reviewed groups of closely related fields.
- Use `sap.field.<object>.<field>` only when a single field is source-reviewed
  enough to stand alone.
- Keep raw SAP technical structure/field names empty until reviewed; do not
  invent technical metadata from memory.
- Store generated bundles, SQLite indexes, JSONL indexes and provider manifests
  under `build/` because they are rebuildable outputs.

## Tracer Bullet

The first merged field atlas item is
`sap.field-set.supplier-invoice-routing`. It links supplier invoice workflow
fields to the supplier invoice object, approval routing field map, and workflow
FO pattern. This proves the intended combined retrieval shape without importing
unreviewed workbook rows.
