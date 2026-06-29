# JSONL authoring contract

`records/*.jsonl` is the canonical agent-facing record surface for SAP Agent Context. Legacy YAML under `knowledge/**/*.yaml` remains an import/authoring convenience while JSONL-native authoring is being migrated.

Machine-readable contract:

```text
schema/jsonl-authoring-contract.yaml
```

## Required authoring guarantees

Each JSONL-native record must preserve:

| Guarantee | Why it matters |
|---|---|
| Stable IDs | Records can be cited from claims, relations, fixtures and downstream bundles. |
| Provenance | Agents can explain where a fact came from and whether it is public, gated or internal-derived. |
| Access labels | Public bundles avoid customer/private/gated leakage. |
| Freshness | Stale and expired evidence remains computable in gates. |
| Compatibility boundary | Existing consumers keep `kind` until `record_type`/`sap_context_type` migration is tested. |

## Current compatibility shape

Item records currently expose:

```json
{"id":"sap.app.example","kind":"sap_app","source_ids":["sap.source.sap-app-example"]}
```

The future shape may add:

```json
{"record_type":"item","sap_context_type":"sap_app"}
```

But that is additive until downstream consumers and roundtrip checks prove the migration. Do not mass-rename `kind` in this slice.

## Legacy YAML boundary

YAML domain packs are still allowed as legacy authoring/import input. They are not canonical runtime state. The durable flow is:

```text
knowledge/**/*.yaml or future JSONL-native authoring
  -> records/*.jsonl
  -> build/context.sqlite + vector corpus
  -> retrieval/evaluation/consumer bundles
```

If YAML and JSONL diverge, fix the import/export or authoring path. Do not make generated SQLite, vector files or build artifacts authoritative.
