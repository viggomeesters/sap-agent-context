# Coverage classification model

This model adapts SDP's evidence-based coverage classification pattern for `sap-agent-context`.

The goal is to avoid binary fake-green. A query or domain can be `ready`, but it can also be `needs_curation`, `source_gap`, `tenant_verification_required`, or `no_source_known`.

## Statuses

| Status | Meaning | Default next action |
|---|---|---|
| `ready` | Evidence and retrieval gates are sufficient for the bounded representative question. | Use with source and tenant caveats. |
| `needs_curation` | Relevant context exists, but quality, precision, freshness or required dimensions are insufficient. | Improve source-labelled context before final use. |
| `source_gap` | No acceptable public/gated/internal-derived evidence exists for the requested claim. | Do not synthesize; discover sources or mark out-of-scope. |
| `tenant_verification_required` | Generic context can explain the concept, but exact behavior requires tenant/live-system evidence. | Answer with caveat and request verification. |
| `no_source_known` | No acceptable repo context/source is known for the topic. | Fail closed and materialize a follow-up if in scope. |

## Required dimensions

Coverage reports and future read models should make these dimensions explicit:

- source traceability;
- freshness;
- retrieval precision;
- required item kinds;
- tenant specificity;
- generated/read-model boundary.

## Boundary

The classification model is a contract for generated reports and gates. It does not import SDP coverage rows and it does not make generated reports authoritative. YAML context and schema files remain the source of truth.
