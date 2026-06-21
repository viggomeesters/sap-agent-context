# SAP FO Knowledge Base

Minimal Technical Product voor een losse, agent-optimized SAP knowledge base
voor Functioneel Ontwerp generatie.

Deze repo is bewust **link-first**. Volledige SAP Help, SAP Notes, Learning Hub
of SAP for Me content wordt niet gespiegeld. De canonical laag bewaart wel:

- source pointers met access-labels (`public`, `gated`, `internal_derived`);
- houdbaarheid per item via `freshness.review_after`;
- korte eigen samenvattingen en claims met evidence;
- relaties naar SAP apps, objecten, rollen, velden, FO-patronen en tests;
- rebuildbare indexen voor CLI/agent-consumptie.

## MTP Scope

De eerste curated domeinset is Supplier Invoice Workflow / J60:

- scope item pointer;
- SAP app pointer;
- SupplierInvoice object anchor;
- AP accountant en manager role anchors;
- field map voor approval routing;
- decision matrix pattern;
- workflow approval FO pattern;
- supplier invoice workflow test pattern;
- public SAP Help source pointer;
- gated SAP for Me/support pointer;
- source access governance pattern.

## Commands

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

`build/vector-corpus.jsonl` is een vector-ready chunk export. Een echte vector
database blijft rebuildbaar en optioneel; de YAML-items blijven source of truth.

## McCoy FO Generator Hook

`mccoy-fo-generator-v2` kan de generated bundle directory zonder codewijziging
registreren als lokale source provider:

```bash
cd /Users/viggomeesters/Dev/mccoy-fo-generator-v2
uv run fo-gen-v2 register-source <workspace> <project-id> \
  --type local-folder \
  --title "SAP FO KB bundle - supplier-invoice workflow" \
  --path "/Users/viggomeesters/Dev/sap-fo-knowledge-base/build/context-bundles" \
  --provenance sap-fo-knowledge-base
```

De bundle zelf bevat `mccoy_integration` metadata en `citations`, zodat de FO
pipeline de KB als traceerbare bron kan meenemen in `sources.yaml`.

## Design Rules

- Canonical waarheid staat in `knowledge/**/*.yaml`.
- Indexen onder `build/` zijn afgeleid en mogen opnieuw worden gemaakt.
- Gated SAP bronnen zijn pointers, geen gecopiede inhoud.
- Customer/project-specifieke kennis hoort niet in de generieke KB zonder
  expliciet access- en tenantlabel.
- Stale items mogen nog vindbaar zijn, maar moeten in bundles als stale worden
  gemarkeerd.
