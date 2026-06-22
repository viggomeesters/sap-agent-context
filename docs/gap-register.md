# Gap Register

Current audit source: `uv run sap-fo-kb audit-completeness`.

## Closed Critical/Important Gaps

| Gap | Severity | Closure evidence |
|---|---:|---|
| No explicit completeness definition | critical | `schema/completeness-matrix.yaml` and this register define bounded scope and audit evidence. |
| Only Supplier Invoice Workflow coverage | critical | `knowledge/domain-packs/sap-fo-starter-coverage.yaml` extends coverage across the representative domains. |
| No machine-verifiable completeness gate | critical | `sap-fo-kb audit-completeness` fails on missing required domains, kinds, access classes or representative bundles. |
| No access-policy knowledge kind | important | `sap.policy.source-access-and-tenant-boundaries` covers public/gated/internal/customer-specific boundaries. |
| Representative bundle coverage unproven | important | Tests and audit representative queries cover workflow, procurement, master data, sales/output and integration/authorization. |

## Later Gaps

These are deliberately outside the current `sap_fo_starter_coverage` definition
of done and should become future scopes, not hidden critical gaps.

| Gap | Reason deferred |
|---|---|
| Exhaustive global SAP product coverage | Too broad for a maintainable starter KB; the current scope targets FO-generation coverage first. |
| Live SAP Help crawling or S-user content ingestion | Requires license, access and governance decisions; current design is link-first. |
| Typed mccoy parsing of `sap_fo_context_bundle` | McCoy can already register bundles as local source providers; typed parsing is the next product iteration. |
| Real vector database service | `build/vector-corpus.jsonl` is vector-ready and rebuildable; service choice is intentionally deferred. |
