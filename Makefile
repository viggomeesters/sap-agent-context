.PHONY: check validate audit evaluate test lint guard diff-check

check: guard validate audit evaluate test lint diff-check

guard:
	uv run python scripts/validate_repository.py

validate:
	uv run sap-agent-context validate

audit:
	uv run sap-agent-context audit-completeness

evaluate:
	uv run sap-agent-context evaluate-fixtures

test:
	uv run pytest -q

lint:
	uv run ruff check .

diff-check:
	git diff --check
