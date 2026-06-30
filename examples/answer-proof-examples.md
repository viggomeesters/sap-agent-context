# SAP Agent Context answer proof examples

These examples show the answer style this repo is trying to make easy for local agents: source-labelled, explicit about uncertainty, and fail-closed on tenant-specific SAP behavior.

They are examples, not customer data and not copied SAP documentation.

## Example 1 — Fiori app tracer answer

**Question**: “Which Fiori app should I use for this process, and can the user access it?”

**Answer shape**:

- **Source**: cite `sap.ref.fiori-apps-reference-library` or a more specific app-library/app source pointer.
- **App anchor**: cite `sap.app.fiori-app-trace-anchor` when only a generic Fiori app trace is available.
- **Trace fields**: carry `Answer.AppName`, `Answer.Citation`, `Answer.AuthorizationEvidence`, `Answer.ProcessContext`, and `Answer.Caveat` from `sap.field-map.fiori-app-traceability`.
- **Fail-closed caveat**: do not claim tenant availability or user access until target business role/catalog assignment and release availability are verified.
- **Follow-up evidence request**: “Send the target business role/catalog or tenant screenshot/export if you need implementation-ready access guidance.”

**Not allowed**: “The app is available to the user” based only on an app name or public app-library pointer.

## Example 2 — Verified Migration Cockpit mapping answer

**Question**: “Can I map Product Number directly in the Migration Cockpit template?”

**Answer shape**:

- **Source**: cite `sap.ref.field-atlas-migration-templates` for the public seed and `sap.ref.sap-help-migration-cockpit-public` as release-verification pointer.
- **Mapping evidence**: carry target key, template version, source owner, transform/value-source, validation artifact, and readiness status via `sap.field-map.migration-verified-mapping-ledger`.
- **Gate**: apply `sap.rule.migration-verified-mapping-ready-gate`.
- **Verdict**: if downloaded template/release evidence or validation artifact is missing, mark `needs_verification_release_template` or `not_ready_missing_validation_artifact`.
- **Tenant caveat**: implementation-ready mapping still requires target template and tenant/release evidence.

**Not allowed**: treating a label-only mapping as verified because the business label sounds familiar.

## Example 3 — Value-source/customizing answer

**Question**: “Can I accept this Company Code value from the source file?”

**Answer shape**:

- **Source/value classification**: cite `sap.object.value-source-classification` and `sap.field-map.value-source-customizing-evidence`.
- **Kind**: classify the value as `customizing`, not a generic identifier.
- **Evidence needed**: target lookup/customizing evidence, allowed values, fallback behavior, and readiness status.
- **Gate**: apply `sap.rule.value-source-customizing-ready-gate`.
- **Verdict**: without target customizing evidence, answer `needs_value_evidence` and ask for target-system proof.

**Not allowed**: accepting source extract values as valid target customizing values without lookup evidence.

## Example 4 — Local query/explain answer

**Question**: “Why did the local query return this SAP context item?”

**Answer shape**:

- **Result id**: name the item id.
- **Rank source**: include exact/FTS/vector source when available.
- **Matched terms**: show terms or evidence that made the result relevant.
- **Claims and sources**: cite claim IDs and source IDs separately.
- **Freshness/access**: include review metadata and access label.
- **Caveat**: if the result is generic/internal-derived, do not present it as tenant evidence.

**Not allowed**: returning fluent prose without IDs, citations, freshness, or ranking explanation.
