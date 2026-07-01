.PHONY: check validate audit audit-v02-gap-report curation-report evaluate build-index build-embeddings evaluate-runtime evaluate-semantic test lint guard diff-check

check: guard validate audit evaluate build-index build-embeddings evaluate-runtime evaluate-semantic test lint diff-check

guard:
	uv run python scripts/validate_repository.py

validate:
	uv run sap-agent-context validate

audit:
	uv run sap-agent-context audit-completeness

audit-v02-gap-report:
	uv run sap-agent-context audit-completeness --matrix schema/sap-agent-context-v0.2-coverage.yaml

curation-report:
	uv run sap-agent-context curation-report \
		--sample-size 3 \
		--output build/reports/content-curation-sample.json

evaluate:
	uv run sap-agent-context evaluate-fixtures

build-index:
	uv run sap-agent-context build-index

build-embeddings:
	uv run sap-agent-context build-embeddings

evaluate-runtime:
	uv run sap-agent-context evaluate-runtime-retrieval

evaluate-semantic:
	uv run sap-agent-context evaluate-semantic-models

test:
	uv run pytest -q

lint:
	uv run ruff check .

diff-check:
	git diff --check
