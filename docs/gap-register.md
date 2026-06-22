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
| Bundles with gaps could still report ready | critical | `build_context_bundle` now returns `needs_curation` whenever bundle gaps exist; adversarial tests cover generic-source-only and stale bundles. |
| Intent-only retrieval could return unrelated bundles | critical | Ranking now requires topic-token evidence; `test_unknown_topic_does_not_return_intent_only_bundle` proves unknown topics do not pass via intent alone. |
| Domains could pass with unusable test-pattern shells | critical | Validator now requires `test_pattern.test_scenarios`; domain pack test patterns include concrete positive/negative scenarios. |
| Field maps could pass without machine-readable fields | important | Validator now requires `field_map` entries or `relations.fields`; missing output/integration/extensibility/analytics fields were added. |
| Public items could cite internal-derived evidence | important | Cross-item evidence validation blocks public items that rely on internal-derived evidence; an actual identity-access claim was fixed. |
| Dutch/English mixed FO queries unproven | important | Synonym expansion and adversarial tests cover mixed Dutch/English supplier-invoice workflow queries. |
| McCoy provider registration might not produce usable context | important | Temp-workspace smoke now verifies both `state/source-providers.yaml` and provider source records in `state/sources.yaml`. |

## Later Gaps

These are deliberately outside the current `sap_fo_starter_coverage` definition
of done and should become future scopes, not hidden critical gaps.

| Gap | Reason deferred |
|---|---|
| Exhaustive global SAP product coverage | Too broad for a maintainable starter KB; the current scope targets FO-generation coverage first. |
| Live SAP Help crawling or S-user content ingestion | Requires license, access and governance decisions; current design is link-first. |
| Typed mccoy parsing of `sap_fo_context_bundle` | McCoy can already register bundles as local source providers; typed parsing is the next product iteration. |
| Real vector database service | `build/vector-corpus.jsonl` is vector-ready and rebuildable; service choice is intentionally deferred. |
