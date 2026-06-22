# Bundle Quality Contract

The starter KB is not complete merely because a bundle contains enough item
kinds. A ready `sap_fo_context_bundle` must provide enough evidence to draft or
review concrete Functioneel Ontwerp sections without hiding source, scope, or
quality gaps.

## Required FO Sections

Every representative bundle should support these FO sections when the intent
requires them:

- Process and scope: selected scope item, app, process-flow or workflow anchor.
- Configuration and app surface: SAP app or configuration surface to inspect.
- Object scope: SAP business object or comparable object anchor.
- Field mapping: source/target or decision-driving fields.
- Business or decision rules: routing, derivation, fallback or exception rules.
- Roles and authorization: business role, catalog, access policy or tenant
  boundary when the intent touches authorizations.
- Test coverage: positive, negative and authorization or exception scenarios.
- Source evidence: public, gated or internal-derived source labels with
  freshness and access metadata.
- Open questions and risks: missing tenant evidence, gated-source checks, stale
  references, and assumptions that a consultant must verify.

## Matrix Dimensions

`schema/completeness-matrix.yaml` defines `required_dimensions` for
representative queries. These dimensions are intentionally higher level than
item kinds. For example, a workflow bundle can require `process_flow` and
`decision_rule`, while an authorization bundle can require `authorization_role`
and `access_policy`.

The completeness audit fails with an important finding when a representative
query is ready by item kind but misses a required quality dimension. This keeps
the current scope honest: the KB remains starter coverage, not exhaustive SAP
product coverage, and a green audit means the starter contract is satisfied at
the bundle level.

## Evidence Integrity

Claim evidence may reference either an existing knowledge item id or a URL. Any
other evidence reference is invalid. Relations that use `sap.*` ids must also
point at existing knowledge items.

Source specificity is explicit when a claim needs more than a root pointer.
Items can set `requires_source_specificity: high` and then must not rely on a
generic SAP Help, SAP for Me or SAP Business Accelerator Hub root URL as their
only source anchor.

Root pointers are still useful starter evidence when they are labeled as
`source.specificity: root_pointer`. Scenario items should add
`release_applicability` when FO correctness can vary by edition, tenant, or
release.

## Retrieval Precision

Representative and adversarial queries must prove scenario precision. A bundle
that collects the right item kinds through broad overlap, but where no selected
item covers enough of the concrete query tokens, is marked `needs_curation`.
The regression corpus lives in `schema/adversarial-query-corpus.yaml`.

## FO Output Evaluation

`schema/fo-output-evaluation-fixtures.yaml` defines deterministic FO-output
fixtures. The evaluator checks whether generated context bundles can satisfy
expected FO section ingredients such as source traceability, required item ids,
field references, test coverage and follow-up gaps for stale, gated or
too-broad queries.

Run it with:

```bash
uv run sap-agent-context evaluate-fixtures
```
