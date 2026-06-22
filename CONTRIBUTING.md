# Contributing

Thank you for considering a contribution. This project is a curated SAP
Functional Design knowledge base, so changes should preserve traceability,
source quality, and deterministic validation.

## Scope

- Keep changes scoped and reviewable.
- Prefer source-backed knowledge additions over inferred content.
- Do not add customer data, screenshots, secrets, private exports, or proprietary
  implementation details.

## Quality

Run the local quality gates before creating a pull request:

```bash
uv run sap-fo-kb validate
uv run sap-fo-kb audit-completeness
uv run sap-fo-kb evaluate-fixtures
uv run pytest -q
uv run ruff check .
```

Add or update tests when behavior changes. For knowledge changes, update the
relevant fixtures or completeness expectations when the change affects retrieval
or context bundle quality.

## PR process

- Explain the SAP scope, source basis, and expected retrieval impact.
- Update documentation for behavior or contract changes.
- Include reproducible validation steps in the pull request description.
