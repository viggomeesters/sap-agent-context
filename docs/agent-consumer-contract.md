# Agent Consumer Contract

SAP Agent Context publishes source-backed context bundles for local AI agents,
McCoy-style generators, and other tools that need SAP implementation context.

## Producer Identity

Generated bundles identify this repository with:

```yaml
producer:
  name: sap-agent-context
  contract: sap-agent-context-bundle
  compatibility_bundle_kind: sap_fo_context_bundle
```

`bundle_kind: sap_fo_context_bundle` remains at the top level for backward
compatibility with existing McCoy integration work. New consumers should key
public-facing behavior from `producer.contract`.

## Local Clone Pattern

Each colleague can use the repository as a local agent context provider:

```bash
git clone <repo-url> sap-agent-context
cd sap-agent-context
uv sync
uv run sap-agent-context query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
```

Consumers can read generated JSON bundles directly or register the
`build/context-bundles/` folder as a local source provider.

## Required Consumer Behavior

- Preserve citations and source access labels in downstream source maps.
- Surface `status`, `gaps`, `quality_signals`, stale items, expired items, and
  gated-source markers before final output generation.
- Treat `ready` as usable context and `needs_curation` as draft-only context
  that requires explicit human acceptance or follow-up.
- Treat expired items as blocked for final use until they are recertified or
  replaced.
- Use `relations.fields`, `relations.objects`, `relations.roles`, claims, and
  summaries to populate field mapping, object scope, authorization, test, and
  decision-rule sections.
- Keep generated bundles as rebuildable artifacts. The canonical source remains
  `records/*.jsonl`; `knowledge/**/*.yaml` is a legacy authoring/import path.
- Follow the [Retrieval trust boundary](retrieval-trust-boundary.md): do not
  promote `needs_curation`, `report_only`, gated, expired or `internal_derived`
  records into customer-specific proof without the required verification.

## McCoy As Example Consumer

McCoy FO Generator v2 can register the bundle folder as a local-folder provider,
but SAP Agent Context is not coupled to McCoy. Other tools can consume the same
JSON bundle contract directly.

See `docs/mccoy-fo-generator-v2-hook.md` for the McCoy-specific command example.
