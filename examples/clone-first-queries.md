# Clone-first Query Examples

Run these after cloning and `uv sync --locked`.

## Full gate

```bash
make check
```

## Ready domain bundles

```bash
uv run sap-agent-context query --intent fo.workflow --topic "supplier invoice approval payment block payment proposal" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.field_mapping --topic "purchase requisition workflow source of supply account assignment purchase order goods receipt" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.integration --topic "integration api communication arrangement credentials tenant url payload business key error handling no secrets" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.business_rules --topic "custom field tenant boundary exposure analytics reporting readiness filter freshness" --sap-product s4hana_cloud_public --limit 12
```

Expected: `status: ready` and `bundle_kind: sap_fo_context_bundle`.

## Fail-closed generic probe

```bash
uv run sap-agent-context query --intent fo.analytics --topic "generic executive dashboard performance report" --sap-product s4hana_cloud_public --limit 12
```

Expected: `status: needs_curation`. Generic dashboard wording should not become ready without concrete query/source/filter/freshness semantics.
