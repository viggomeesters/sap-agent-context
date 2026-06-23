# SDP pattern adoption ledger

This ledger records public-repo-compatible architecture patterns adopted from the private Smart Data Platform (SDP) repository into `sap-agent-context`.

## Boundary

`sap-agent-context` remains a public, generic SAP context repository. The canonical source of truth remains the YAML context under `knowledge/`, `schema/`, and related repository metadata unless a future ADR explicitly changes that boundary.

Adoption from SDP is **pattern-only**:

- no customer/client names;
- no project identifiers or project registry content;
- no XLSX contents;
- no field-usage history or analytics rows;
- no internal URLs;
- no secrets;
- no proprietary mappings;
- no copied SAP documentation.

Default for every row below: `copied_code=false`. If a future task copies code, it must add exact provenance, license, minimized diff scope, and a public-safety review before merge.

## Adopted pattern ledger

| Pattern | Provenance | License | copied_code | ideas_extracted | applied_in | Boundary decision |
|---|---|---|---:|---|---|---|
| SSOT/read-model boundary | Private SDP README and Data README architecture notes | MIT-labelled source repo; pattern description only | false | Keep editable source data authoritative; generated DB/JSON/SQLite/report artifacts are derived and rebuildable. | `docs/sdp-pattern-adoption-ledger.md`; future read-model tasks | Adopt as architectural rule; no SDP data copied. |
| Layered model | Private SDP Data README layered data model | MIT-labelled source repo; pattern description only | false | Organize context evolution by layers: source pointers, objects/aliases/relations, field/context items, coverage/gates, generated reports. | Future schema/docs tasks in this plan | Adopt as conceptual model, not as SDP folder/data mirror. |
| Identity / alias / relation contracts | Private SDP schema module table definitions for objects, aliases, relations, field identity | MIT-labelled source repo; pattern description only | false | Make object identity, aliases, relations and field identity explicit, testable contracts. | `schema/identity-alias-relation-contract.yaml`; `docs/identity-alias-relation-contract.md` | Adopt contract shape only; no object rows or aliases copied. |
| Manifest and source catalog discipline | Private SDP README template library/source-boundary notes | MIT-labelled source repo; pattern description only | false | Track source/template manifests and checksums/provenance for generated or derived artifacts. | Planned child `source-template-manifest-pattern` | Adopt manifest habit; no template files or manifest rows copied. |
| Coverage classification | Private SDP coverage generation script classification pattern | MIT-labelled source repo; pattern description only | false | Classify coverage by evidence status and next action instead of binary ready/not-ready claims. | Planned child `coverage-classification-model` | Adopt status vocabulary concept; no SDP coverage rows copied. |
| Generated reports | Private SDP README build/report workflow | MIT-labelled source repo; pattern description only | false | Provide rebuildable generated reports for humans while keeping canonical data in source files. | Planned child `generated-docs-reports-command` | Adopt generated-report boundary; generated outputs are not SSOT. |
| Validation gates | Private SDP README/generation workflow and sap-agent-context existing `make check` | MIT-labelled source repo; pattern description only | false | Treat rebuild, validation, fixtures, tests and diff checks as adoption gates. | Current and future plan children | Adopt gate discipline; no private scripts copied. |

## Rejected / deferred patterns

| Pattern | Decision | Reason |
|---|---|---|
| Copying SDP CSV/XLSX/schema data | rejected | Public repo boundary: would risk private/customer/project data and would not belong in generic SAP context. |
| Treating generated SQLite/JSON/read models as writable source of truth | rejected | `sap-agent-context` must keep canonical public YAML/metadata as SSOT unless a future ADR approves migration. |
| Importing SDP project/customer analytics | rejected | Field usage, project registry and customer decisions are private and not generic SAP context. |
| Mirroring SDP's full data layer | deferred/rejected for this loop | Useful architectural inspiration, but too broad and would blur scope. Adopt only narrow contracts with tests. |

## Required checks for future adoption children

Every child that adopts one of these patterns must preserve:

1. `bundle_kind: sap_fo_context_bundle` compatibility.
2. Public-safe source labels and freshness metadata where knowledge items are added.
3. Generated/read-model labels on derived artifacts.
4. Representative query statuses from `sap-agent-context evaluate-fixtures`.
5. A review note proving no SDP private data, XLSX contents, internal URLs, secrets or proprietary mappings were copied.
