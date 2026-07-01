# SAP Agent Context coverage heatmap

> Generated from current knowledge items. This is a planning heatmap, not an exhaustive SAP product coverage claim.

Total items: `666`

## Domain density

| Domain | Items | Sources | FO patterns | Decision rules | Test patterns | Eval items |
|---|---:|---:|---:|---:|---:|---:|
| analytics_extensibility | 35 | 4 | 0 | 5 | 6 | 9 |
| eam_pm | 121 | 12 | 9 | 21 | 12 | 13 |
| finance | 77 | 8 | 3 | 11 | 9 | 11 |
| integration | 284 | 39 | 11 | 27 | 30 | 31 |
| material_master | 97 | 9 | 3 | 8 | 8 | 11 |
| migration | 209 | 10 | 0 | 22 | 25 | 48 |
| procurement | 100 | 12 | 1 | 15 | 15 | 19 |
| sales_otc | 204 | 20 | 10 | 23 | 23 | 27 |
| security_authorizations | 358 | 44 | 3 | 26 | 30 | 32 |
| unclassified | 4 | 1 | 0 | 1 | 1 | 1 |

## EAM/PM lifecycle slices

| Slice | Items | FO patterns | Decision rules | Test patterns | Status |
|---|---:|---:|---:|---:|---|
| equipment | 61 | 5 | 8 | 7 | dense |
| functional-location | 16 | 1 | 2 | 2 | dense |
| notification | 17 | 3 | 2 | 1 | dense |
| maintenance-order | 28 | 3 | 4 | 3 | dense |
| maintenance-plan | 10 | 1 | 2 | 1 | dense |
| task-list | 11 | 2 | 2 | 1 | dense |
| measuring-point-counter | 9 | 1 | 2 | 1 | dense |
| work-center | 12 | 1 | 2 | 1 | dense |
| bom-spares | 26 | 3 | 4 | 2 | dense |
| confirmation | 22 | 1 | 6 | 4 | dense |
| technical-completion | 11 | 1 | 2 | 2 | dense |
| settlement | 9 | 1 | 2 | 1 | dense |
| permits-safety | 3 | 0 | 1 | 1 | thin |

## Weak domains

- **analytics_extensibility**: Missing or thin FO patterns.
- **migration**: Missing or thin FO patterns.

## Contract

- `records/*.jsonl` remains the canonical agent record surface.
- YAML is legacy authoring/import format only.
- This heatmap should guide filling; it must not become a fake exhaustive SAP completeness claim.

## Maturity report

Run:

```bash
uv run sap-agent-context maturity-report --output build/reports/maturity-report.json
```

The maturity report maps observed domains and declared density profiles to the
same deep-domain template dimensions: source references, domain anchors, FO
patterns, decision rules, test patterns, and runtime/evaluation coverage. It
separates `required`, `report_only`, and `needs_curation` states; it remains a
planning signal, not an exhaustive SAP product truth claim.

For concrete follow-up candidates by slice, run:

```bash
uv run sap-agent-context gap-report --output build/reports/gap-report.json
```

Each missing dimension becomes a follow-up task candidate with acceptance text;
slices without gaps carry an explicit no-follow-up reason.
