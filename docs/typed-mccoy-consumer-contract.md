# Typed McCoy Consumer Contract

This repository publishes `sap_fo_context_bundle` JSON. McCoy can keep using the
bundle directory as a local-folder source provider, but the preferred next step
is typed parsing of the bundle payload.

## Versioning

Bundles include `schema_version: 1` and `bundle_kind:
sap_fo_context_bundle`. Consumers should ignore unknown keys, reject unsupported
schema versions, and keep backward compatibility for the current local-folder
registration path.

The human-readable schema is
`schema/sap-fo-context-bundle.schema.yaml`.

## Readiness Semantics

- `ready`: the bundle has selected items and no known gaps.
- `needs_curation`: McCoy may use the bundle for planning or draft context, but
  final FO generation should surface or block on the listed `gaps`.

McCoy should not treat item presence as enough. It should also inspect
`quality_signals`, especially `gap_count`, `stale_count`, `gated_item_count`,
`source_url_count`, `access_labels`, and `item_kind_counts`.

## Consumption Rules

- Preserve `citations` in downstream source maps.
- Keep item `access`, `requires_login`, `review_after`, and `stale` visible to
  the planner and reviewer.
- Use `relations.fields`, `relations.roles`, `relations.objects`, claims and
  summaries to populate FO field mapping, authorization, object scope, test and
  decision-rule sections.
- Treat gated sources as verification pointers, not copied evidence.
- Treat stale items as recertification work before final delivery.

## Backward Compatibility

`docs/mccoy-fo-generator-v2-hook.md` remains valid. Registering the generated
bundle folder as a local-folder provider is still supported while typed parsing
is implemented downstream.

## Out Of Scope

This task does not modify `mccoy-fo-generator-v2`. The downstream work is a
separate McCoy task: parse `sap_fo_context_bundle` directly and inject selected
items, citations and quality signals into the typed FO planner.
