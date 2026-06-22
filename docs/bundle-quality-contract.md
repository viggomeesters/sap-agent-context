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
