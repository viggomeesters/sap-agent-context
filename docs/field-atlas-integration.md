# SAP Field Atlas Integration

This repository is now the canonical `sap-agent-context` target. The public
`viggomeesters/sap-field-atlas` repository is treated as a real upstream/public
source, not as a hypothetical local folder.

## Source inspected

- Upstream/public: <https://github.com/viggomeesters/sap-field-atlas>
- WSL clone used for merge review: `/home/viggo/Dev/sap-field-atlas`
- Canonical target: `/home/viggo/Dev/sap-agent-context`

## Merged into SAP Agent Context

The Field Atlas material absorbed here is small and generic:

- `MARA-MATNR` as the Material Master / Product Number identifier context.
- `T001-BUKRS` as the Company Code customizing/value-source context.
- MARA and T001 table/object anchors.
- SE16N/SE11 usage preserved as source context in the upstream pointer and as
  agent retrieval terms, not as copied operational documentation.
- The `s4-product-initial-seed` Product Number → MARA-MATNR mapping note,
  explicitly marked `needs_verification`.
- The BUKRS customizing value-source warning.

Concrete canonical items:

- `knowledge/source-registry/sap-field-atlas-public.yaml`
- `knowledge/sap-objects/master-data-field-atlas.yaml`
- `knowledge/fields/core-master-data-field-atlas.yaml`
- `knowledge/field-maps/product-number-migration-seed.yaml`

All imported items keep `freshness.expires_at`, source URLs, access labels, and
verification caveats.

## Preserved in SAP Agent Context

SAP Agent Context remains responsible for:

- the agent consumer contract;
- source/freshness/access metadata;
- FO workflow and context-bundle generation;
- bundle readiness semantics including stale/expired item handling;
- McCoy/local-folder integration examples.

## Absorption contract

The canonical concept mapping is maintained in:

- `schema/field-atlas-absorption-contract.yaml`

That contract maps archived Field Atlas concepts into SAP Agent Context without
reintroducing Field Atlas as a runtime package:

- transactions → `sap_app` / `external_reference` retrieval aliases;
- tables → `sap_object` anchors;
- fields → `sap_field` and `field_map` items;
- domains/value sources → caveats, `sap_field` details or `decision_rule` items;
- relationships → cross-item `relations`, not a separate graph package;
- migration templates → `field_map`, `sap_object`, and `test_pattern` context
  with release/verification caveats;
- Fiori apps → `sap_app`, `sap_role`, and `access_policy` context only when a
  source-backed app/catalog/role pointer exists.

## Not merged

The following Field Atlas surfaces are intentionally not copied into the
canonical package:

- The standalone `sap_field_atlas` Python package and CLI.
- The standalone Field Atlas schemas as first-class runtime schemas.
- Public repo-complete/governance files that are not needed for runtime context.
- Generated build artifacts.
- Any private/client data — none was observed in the inspected public source.

## Legacy repository strategy

Current public state:

1. `viggomeesters/sap-agent-context` is the canonical clone target for agents.
2. `viggomeesters/sap-field-atlas` is archived public legacy/provenance seed.
3. The archived GitHub URL stays alive as a source pointer; if it disappears,
   update `knowledge/source-registry/sap-field-atlas-public.yaml` and related
   freshness metadata before relying on the absorbed context.
