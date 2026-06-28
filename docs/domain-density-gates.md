# Domain-density gates

`audit-completeness` now reports bounded domain-density profiles in addition to the starter coverage gate.

This is not an exhaustive SAP product coverage claim. It is a guard against shallow green: a domain can have starter coverage while still missing the sources, FO patterns, decision rules, test patterns or eval fixtures needed for implementation-pack work.

## Levels

- `starter`: enough anchors for lookup/navigation or early FO context, but missing one or more deep-profile dimensions.
- `deep`: the selected profile meets bounded thresholds for item count, source references, FO patterns, decision rules, test patterns and eval/retrieval fixture coverage.

## Promotion

Profiles default to `report_only`. Missing dimensions create `later` findings and do not fail the starter gate. A profile only fails `audit-completeness` when its matrix entry sets `promotion: required` and a threshold is missed.

Current promoted deep slice:

- `eam_pm_lifecycle`: EAM/PM lifecycle implementation-pack coverage built from the heatmap, lifecycle spine, FO patterns and retrieval fixtures.

Current report-only weak slice:

- `analytics_extensibility_candidate`: names a shallow area without blocking existing starter coverage.

Use `uv run sap-agent-context audit-completeness` and inspect `domain_density_profiles` in the JSON output.

## Creating a new deep slice

Use [Deep domain pack template](deep-domain-pack-template.md) and
`examples/deep-domain-pack-template.yaml` for future slices. New slices should
start with `promotion: report_only`; promote to `required` only after source
references, FO patterns, decision rules, test patterns, FO-output fixtures,
runtime retrieval fixtures, semantic fixtures, and bounded thresholds are all
present and tested.

The promotion boundary is deliberately narrow: a `deep` profile means bounded
implementation-pack coverage for that named slice, not exhaustive SAP product
coverage.
