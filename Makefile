.PHONY: check validate audit audit-v02-gap-report evaluate test lint guard diff-check

check: guard validate audit evaluate test lint diff-check

guard:
	uv run python scripts/validate_repository.py

validate:
	uv run sap-agent-context validate

audit:
	uv run sap-agent-context audit-completeness

audit-v02-gap-report:
	-uv run sap-agent-context audit-completeness --matrix schema/sap-agent-context-v0.2-coverage.yaml

evaluate:
	uv run sap-agent-context evaluate-fixtures

test:
	uv run pytest -q

lint:
	uv run ruff check .

diff-check:
	git diff --check
