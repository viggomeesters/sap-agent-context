# Context bundle consumer contract

`build_context_bundle` returns a local JSON contract for downstream agents and FO tools. The bundle is designed for safe consumption: it carries status, selected records, citations, gaps and quality signals instead of asking consumers to infer readiness from fluent text.

## Top-level fields

| Field | Meaning | Consumer rule |
|---|---|---|
| `schema_version` | Integer schema version for this JSON shape. | Reject or adapt unknown future versions. |
| `bundle_kind` | Compatibility kind, currently `sap_fo_context_bundle`. | Keep for older McCoy-style consumers. |
| `consumer_contract` | Machine-readable contract name, version, statuses and required fields. | Check before rendering customer-facing output. |
| `producer` | Producer identity and compatibility contract name. | Preserve in provenance/source maps. |
| `generated_at` | UTC generation timestamp. | Treat bundle as rebuildable runtime output. |
| `query` | Intent/topic/product/limit used to select context. | Show this when output seems off-topic. |
| `status` | `ready` or `needs_curation`. | `ready` can be used as starter context; `needs_curation` is draft-only. |
| `items` | Selected source-backed records with freshness/access metadata. | Cite item IDs and source metadata; do not drop gaps. |
| `citations` | Compact citation list for selected items. | Preserve access labels and retrieved timestamps. |
| `gaps` | Blocking or cautionary reasons. | Surface before final output; do not hide them. |
| `quality_signals` | Counts for gaps, stale/expired items, gated items, source URLs and item kinds. | Use as guardrails, not as quality theater. |
| `mccoy_integration` | Local-folder registration hint. | Optional convenience for McCoy consumers. |

## Status semantics

`status` has two final bundle values:

- `ready`: no bundle gaps were detected for the selected records. Consumers may use it as starter context while preserving citations, access, freshness and caveats.
- `needs_curation`: the bundle is not final-use ready. Consumers must show gaps and ask for curation/human acceptance/follow-up before generating customer-facing claims.

`report_only` is not a final bundle status. In machine-readable contract text,
`report_only is not a final bundle status` means it is a domain/profile maturity
state from `maturity-report` and `audit-completeness`. A `report_only` slice may
still appear inside selected records, but consumers must not promote it to
`ready` without the deep-domain gates.

## Item provenance fields

Each item includes:

```json
{
  "id": "sap.app.eam.pm.ie03",
  "kind": "sap_app",
  "access": "public",
  "review_after": "2026-12-23",
  "expires_at": "2027-06-23",
  "stale": false,
  "expired": false,
  "source": {
    "kind": "public_doc",
    "title": "SAP Help reference",
    "url": "https://example.invalid",
    "retrieved_at": "2026-06-01",
    "license_note": "link-only"
  },
  "claims": [],
  "relations": {}
}
```

Consumer expectations:

- preserve `id`, `kind`, `access`, `source`, `claims` and `relations` in source maps;
- treat `stale=true` as recertification needed;
- treat `expired=true` as blocked for final use;
- treat `gated` and `internal_derived` as non-public proof labels;
- do not invent source URLs or customer/tenant evidence when missing.

## Gap semantics

Gaps are user-facing blockers or cautions. Examples:

- no test pattern selected;
- no SAP app/object/field map selected;
- only gated/internal sources selected;
- selected items are stale or expired;
- topic precision is too low.

A consumer may still use a `needs_curation` bundle for brainstorming or planning, but not as final customer-facing proof.

## Contract check example

```python
required = {"status", "items", "citations", "gaps", "quality_signals"}
missing = required - bundle.keys()
if missing:
    raise ValueError(f"missing required bundle fields: {sorted(missing)}")
if bundle["status"] != "ready":
    print("Draft only; surface gaps before output:", bundle["gaps"])
```

See `examples/downstream-consumer-fixtures.json` for ready, `needs_curation`,
`report_only`, and anti-hallucination response examples.

Consumer fail-closed gate fixtures live in
`schema/consumer-fail-closed-fixtures.yaml`. They intentionally catch missing
source, missing source output, missing tenant evidence, hidden gaps, `needs_curation` misuse and
`report_only` misuse (report_only misuse) before a consumer treats draft context as final output.

## Boundary

The contract proves the repository produced a bounded, source-labelled context bundle. It does not prove exhaustive SAP coverage, tenant configuration, proprietary documentation access, or customer-specific correctness.
