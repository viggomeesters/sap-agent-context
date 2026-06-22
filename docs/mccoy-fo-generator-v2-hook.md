# McCoy FO Generator v2 Hook Contract

This document shows `mccoy-fo-generator-v2` as one example consumer for SAP
Agent Context. The repository is a general local SAP context provider for AI
agents; McCoy integration is not the only supported use case.

## Producer Contract

Run in deze repo:

```bash
uv run sap-agent-context validate
uv run sap-agent-context build-index
uv run sap-agent-context audit-completeness
uv run sap-agent-context query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
uv run sap-agent-context mccoy-provider \
  build/context-bundles/supplier-invoice-workflow.json \
  --title "SAP Agent Context bundle - supplier-invoice workflow" \
  --output build/context-bundles/mccoy-provider.json
```

The context bundle has:

- `producer.name: sap-agent-context`;
- `producer.contract: sap-agent-context-bundle`;
- `bundle_kind: sap_fo_context_bundle`
- selected `items` with claims, relations, freshness and access labels;
- `citations` with public/gated/internal source markers;
- `gaps` for missing or stale evidence;
- `mccoy_integration` with the recommended provider type.

## Consumer Contract

Register the generated bundle folder in a McCoy workspace. The folder can hold
one bundle or all representative bundles:

```bash
cd /Users/viggomeesters/Dev/mccoy-fo-generator-v2
uv run fo-gen-v2 register-source <workspace> <project-id> \
  --type local-folder \
  --title "SAP Agent Context bundle - supplier-invoice workflow" \
  --path "/Users/viggomeesters/Dev/sap-agent-context/build/context-bundles" \
  --provenance sap-agent-context
```

Current `mccoy-fo-generator-v2` stores this in
`projects/<project-id>/state/source-providers.yaml`. During context collection,
the folder becomes a source record in `sources.yaml` and can be surfaced in plan
and draft source maps.

## Next Integration Step

The next non-MTP step is to teach `mccoy-fo-generator-v2` to parse
`sap-agent-context-bundle` JSON directly and inject selected context items into
the typed planner, instead of treating the bundle only as a local source folder.

See `docs/agent-consumer-contract.md`, `docs/typed-mccoy-consumer-contract.md`, and
`schema/sap-agent-context-bundle.schema.yaml` for the context-side typed contract.
