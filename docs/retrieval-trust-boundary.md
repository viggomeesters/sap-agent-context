# Retrieval trust boundary

SAP Agent Context retrieval output is evidence-ranked context, not SAP product truth. Consumers must preserve the difference between ready context, draft-only context and missing evidence.

## What retrieval can prove

A runtime or bundle result can prove that the repository contains a matching record with:

- a stable record id;
- `kind` / context type;
- source IDs, claim IDs and relation IDs;
- access label: `public`, `gated` or `internal_derived`;
- freshness metadata such as `review_after` and `expires_at`;
- ranking explanation such as matched terms, rank source, BM25/vector metadata and focus boost;
- bundle status and gaps when generated through `sap-agent-context query`.

This is enough to draft or review bounded FO sections when the bundle status is `ready` and no blocking freshness/access gaps exist.

## What retrieval cannot prove

Retrieval output does **not** prove:

- exhaustive SAP product coverage;
- tenant-specific configuration, customizing, roles, field availability or workflow variants;
- that gated SAP Help, SAP for Me, Learning Hub or SAP Notes content was actually visible to the consumer;
- that an `internal_derived` consultant rule is customer proof;
- that a generic or broad query is implementation-ready just because some records ranked.

When a result is ambiguous, stale, expired, gated without verification or tenant-specific, consumers must fail closed and ask for evidence instead of filling the gap with generic SAP prose.

## Status boundaries

| Status / signal | Consumer behavior |
|---|---|
| `ready` | Usable as starter context when citations, freshness and access labels are preserved. |
| `needs_curation` | Draft-only. Surface gaps and ask for curation or human acceptance before final output. |
| `report_only` slice | Useful for gap/maturity reporting, not product-ready coverage. Do not promote it to ready without required gates. |
| stale `review_after` | Mark as needing recertification before final use. |
| expired `expires_at` | Block final use until replaced or recertified. |
| `gated` source | Tell the user the source needs login/verification; do not imply public proof. |
| `internal_derived` | Treat as consultant heuristic; verify in target tenant/system before customer-specific claims. |

## Consumer-facing citation expectation

A consumer using runtime-search or generated bundles should keep at least this trace in the output or source map:

```json
{
  "record_id": "sap.rule.procurement-release-strategy-tenant-evidence",
  "status": "ready",
  "access": "internal_derived",
  "freshness": {"review_after": "2026-12-23", "expires_at": "2027-06-23"},
  "source_ids": ["sap.source.sap-rule-procurement-release-strategy-tenant-evidence"],
  "claim_ids": ["sap.claim.sap-rule-procurement-release-strategy-tenant-evidence.001"],
  "trust_note": "Use as starter guidance; verify release conditions, workflow variant, approver roles, thresholds and fallback owner in the tenant."
}
```

If source IDs or claim IDs are missing for a final customer-facing claim, the consumer should mark the section as open rather than inventing provenance.

## Fail-closed examples

- Generic dashboard request: keep broad analytics/reporting results as `needs_curation` unless selected items cover the concrete KPI/source/filter/freshness tokens.
- Invented tenant field: do not create authority for a `ZZZ_*` field unless source/customer/tenant evidence exists.
- Unrelated module: HR/payroll or other out-of-scope prompts must not be answered with EAM/PM, procurement or analytics records simply because a few generic terms overlap.

These cases are represented in `schema/runtime-retrieval-fixtures.yaml` so regressions fail during `uv run sap-agent-context evaluate-runtime-retrieval`.

## No exhaustive truth claim

A green retrieval gate means the bounded starter contract passed for the current fixtures. It does not mean SAP Agent Context covers all SAP products, releases, tenants, localizations or customer variants. Consumers must keep open questions visible when the repository only provides starter context.
