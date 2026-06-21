# McCoy FO Generator v2 Hook Contract

Deze MTP integreert met `mccoy-fo-generator-v2` via bestaande source-provider
mechaniek. De generator hoeft hiervoor nog niet aangepast te worden.

## Producer Contract

Run in deze repo:

```bash
uv run sap-fo-kb validate
uv run sap-fo-kb build-index
uv run sap-fo-kb query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
uv run sap-fo-kb mccoy-provider \
  build/context-bundles/supplier-invoice-workflow.json \
  --title "SAP FO KB bundle - supplier-invoice workflow" \
  --output build/context-bundles/mccoy-provider.json
```

The context bundle has:

- `bundle_kind: sap_fo_context_bundle`
- selected `items` with claims, relations, freshness and access labels;
- `citations` with public/gated/internal source markers;
- `gaps` for missing or stale evidence;
- `mccoy_integration` with the recommended provider type.

## Consumer Contract

Register the generated bundle folder in a McCoy workspace:

```bash
cd /Users/viggomeesters/Dev/mccoy-fo-generator-v2
uv run fo-gen-v2 register-source <workspace> <project-id> \
  --type local-folder \
  --title "SAP FO KB bundle - supplier-invoice workflow" \
  --path "/Users/viggomeesters/Dev/sap-fo-knowledge-base/build/context-bundles" \
  --provenance sap-fo-knowledge-base
```

Current `mccoy-fo-generator-v2` stores this in
`projects/<project-id>/state/source-providers.yaml`. During context collection,
the folder becomes a source record in `sources.yaml` and can be surfaced in plan
and draft source maps.

## Next Integration Step

The next non-MTP step is to teach `mccoy-fo-generator-v2` to parse
`sap_fo_context_bundle` JSON directly and inject selected KB items into the typed
planner, instead of treating the bundle only as a local source folder.
