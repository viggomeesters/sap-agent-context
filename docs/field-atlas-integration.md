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

## Not merged

The following Field Atlas surfaces were intentionally not copied into the
canonical package in this pass:

- The standalone `sap_field_atlas` Python package and CLI.
- The standalone Field Atlas schemas as first-class runtime schemas.
- Public repo-complete/governance files that are not needed for runtime context.
- Generated build artifacts.
- Any private/client data — none was observed in the inspected public source.

## Legacy repository strategy

Preferred public-state after this merge:

1. `viggomeesters/sap-agent-context` is the canonical clone target for agents.
2. `viggomeesters/sap-field-atlas` can remain public as a legacy seed/source
   package, but its README should point readers to `sap-agent-context` for the
   canonical agent-consumable bundle contract.
3. If the Field Atlas repository is archived later, keep the GitHub URL alive as
   a source pointer and update freshness metadata in this repository.
