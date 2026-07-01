# Agent Instructions — SAP Agent Context

SAP Agent Context is a public, generic, agent-first SAP context repository. It is
not a client project archive and not a full SAP knowledge-base mirror.

## Repo identity

- Public repo: `viggomeesters/sap-agent-context`
- Python package: `sap-agent-context`
- Python module: `sap_agent_context`
- CLI: `sap-agent-context`
- Public bundle contract: `sap-agent-context-bundle`
- Compatibility bundle kind: `sap_fo_context_bundle`

Do not reintroduce old package/project/schema slugs. The only allowed old
identifier is the explicit runtime compatibility value `sap_fo_context_bundle`.

## Public data boundary

Allowed:

- generic SAP table, field, workflow, role, scope item, migration and functional
  design context;
- public source references and access-labelled gated pointers;
- explicitly confidence-labelled consultant knowledge;
- synthetic examples that contain no customer data.

Forbidden:

- customer/client names;
- screenshots or exports from SAP systems;
- internal URLs, tickets, project IDs, proprietary mappings;
- copied proprietary SAP documentation;
- secrets, credentials, cookies, `.env` files, or private keys.

## Workflow

1. Inspect `git status --short --branch` and `git remote -v` before editing.
2. Keep changes data-first, source-labelled, freshness-labelled and reviewable.
3. Run `make check` before finishing.
4. Commit focused changes after gates pass.
5. Push to the public repo only when that external/public write is intended.

## Validation contract

`make check` runs:

- repository identity/safety guard;
- YAML knowledge validation;
- starter completeness audit;
- FO-output evaluation fixtures;
- runtime index and embedding builds;
- runtime retrieval and semantic model evaluations;
- pytest regression tests;
- Ruff lint;
- git whitespace diff check.

`make audit-v02-gap-report` is a separate fail-hard campaign gate for
`schema/sap-agent-context-v0.2-coverage.yaml`; it must return a non-zero exit
when the v0.2 matrix reports blocking findings.
