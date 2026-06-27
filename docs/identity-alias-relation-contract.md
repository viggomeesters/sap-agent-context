# Identity, alias and relation contract

This contract adapts safe SDP identity/alias/relation patterns for `sap-agent-context` without importing SDP data.

## Intent

Agents need stable IDs, searchable aliases and explicit relations so context bundles can be generated deterministically and reviewed safely. The canonical source of truth is the JSONL record surface under `records/*.jsonl`; generated indexes and reports are derived read models, and YAML is only a legacy authoring/import format.

## Identity

- `id` is the canonical item key.
- IDs are stable public-repo identifiers, not generated database row IDs.
- Generated artifacts may copy IDs for lookup, but may not rewrite them.
- Compatibility value `bundle_kind: sap_fo_context_bundle` remains preserved for downstream consumers.

## Aliases

Aliases are discovery hints only. They may live in `topics`, explicit alias fields, or source synonym metadata when the schema supports it.

Alias rules:

1. use generic SAP/public-safe terms;
2. do not include customer names, project identifiers, internal URLs or tenant-specific labels;
3. do not imply implementation readiness without source-labelled evidence;
4. keep aliases subordinate to the canonical item id.

## Relations

Relations connect canonical item IDs such as objects, fields, apps, source references, rules and test patterns. Relations improve retrieval and traceability, but they do not prove tenant configuration.

Relation rules:

1. relation targets should resolve to existing IDs where validation supports the relation group;
2. relation descriptions must stay generic and public-safe;
3. relation presence means relevant context, not live system proof.

## Field identity

Field identity keeps these concerns separate:

- business term or consultant-facing label;
- SAP technical structure/field reference where available;
- mapping/defaulting/business-rule guidance;
- tenant or project-specific decision evidence.

Generic context may explain field semantics, but it must not invent tenant-specific mandatory/optional status, transform method, default value, storage location, movement type or project decision.

## Boundary from SDP

Adopted from SDP pattern concepts only:

- object identity;
- aliases;
- relations;
- field identity;
- generated read-model separation.

Not adopted:

- SDP object rows;
- aliases or relation rows;
- customer/project analytics;
- XLSX contents;
- field usage history;
- private paths, URLs or proprietary mappings.
