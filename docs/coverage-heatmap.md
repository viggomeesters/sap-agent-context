# SAP Agent Context coverage heatmap

> Generated from current knowledge items. This is a planning heatmap, not an exhaustive SAP product coverage claim.

Total items: `637`

## Domain density

| Domain | Items | Sources | FO patterns | Decision rules | Test patterns | Eval items |
|---|---:|---:|---:|---:|---:|---:|
| analytics_extensibility | 35 | 4 | 0 | 5 | 6 | 9 |
| eam_pm | 92 | 10 | 3 | 14 | 11 | 12 |
| finance | 74 | 8 | 2 | 10 | 9 | 11 |
| integration | 282 | 39 | 10 | 27 | 30 | 31 |
| material_master | 97 | 9 | 3 | 8 | 8 | 11 |
| migration | 209 | 10 | 0 | 22 | 25 | 48 |
| procurement | 100 | 12 | 1 | 15 | 15 | 19 |
| sales_otc | 204 | 20 | 10 | 23 | 23 | 27 |
| security_authorizations | 355 | 44 | 2 | 25 | 30 | 32 |
| unclassified | 4 | 1 | 0 | 1 | 1 | 1 |

## EAM/PM lifecycle slices

| Slice | Items | FO patterns | Decision rules | Test patterns | Status |
|---|---:|---:|---:|---:|---|
| equipment | 57 | 3 | 7 | 6 | dense |
| functional-location | 14 | 0 | 1 | 2 | thin |
| notification | 12 | 1 | 1 | 1 | dense |
| maintenance-order | 18 | 0 | 3 | 3 | thin |
| maintenance-plan | 0 | 0 | 0 | 0 | missing |
| task-list | 0 | 0 | 0 | 0 | missing |
| measuring-point-counter | 0 | 0 | 0 | 0 | missing |
| work-center | 0 | 0 | 0 | 0 | missing |
| bom-spares | 20 | 1 | 2 | 2 | dense |
| confirmation | 18 | 0 | 5 | 4 | thin |
| technical-completion | 4 | 0 | 1 | 1 | thin |
| settlement | 0 | 0 | 0 | 0 | missing |
| permits-safety | 0 | 0 | 0 | 0 | missing |

## Weak domains

- **analytics_extensibility**: Missing or thin FO patterns.
- **migration**: Missing or thin FO patterns.

## Contract

- `records/*.jsonl` remains the canonical agent record surface.
- YAML is legacy authoring/import format only.
- This heatmap should guide filling; it must not become a fake exhaustive SAP completeness claim.
