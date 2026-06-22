# Completeness Matrix

This KB is complete for the current goal when it has no known critical or
important gaps inside the `sap_fo_starter_coverage` scope defined in
`schema/completeness-matrix.yaml`.

The scope is intentionally bounded: it is not a claim of exhaustive SAP product
coverage. It is the starter coverage required for McCoy FO generation across
representative SAP implementation domains.

Covered dimensions:

- Domains: finance/AP, procurement, sales, master data, migration, workflow,
  output, authorizations, integrations, extensibility, analytics/reporting.
- Knowledge kinds: external references, scope items, SAP apps, SAP objects,
  SAP roles, field maps, decision rules, FO patterns, test patterns and access
  policies.
- Governance: source access, gated SAP pointers, review dates, release
  applicability through `sap_product`, confidence through source/access labels,
  and claim evidence.
- Consumer readiness: context bundles, McCoy source-provider compatibility and
  a future typed reader path.
- Quality: schema validation, completeness audit, retrieval/bundle tests, stale
  source behavior and gated-source behavior.

Audit command:

```bash
uv run sap-agent-context audit-completeness
```

The command must report `status: passed` with zero critical and zero important
findings before this KB may claim no known gaps in the current scope.
