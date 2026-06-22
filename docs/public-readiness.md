# Public Readiness

SAP Agent Context is intended to be published as a professional public GitHub
project after a remote is connected.

## Current Status

- Source code, tests, documentation, license, security policy, contribution
  guide, changelog, CI workflow, and repository visual assets are present.
- No `.env`, private key, token, private screenshot, customer export, or large
  binary artifact is stored in the current repository files.
- No GitHub remote is configured yet, so GitHub visibility, About metadata,
  topics, and releases cannot be verified locally.

## Privacy Review Notes

Automated filename checks may flag paths containing `supplier-invoice`. In this
repository those files are generic SAP process examples used for Functional
Design bundle tests. They are not real supplier invoices, customer records,
screenshots, or proprietary client artifacts.

Before publishing, run a final manual review for:

- credentials, `.env` files, API keys, private keys, and tokens;
- customer-specific SAP tenant data;
- copied SAP Help, SAP Notes, Learning Hub, or SAP for Me content;
- private screenshots or binary attachments;
- proprietary client names or implementation data.

## Publish Checklist

1. Create a public GitHub repository.
2. Add the remote and push:

   ```bash
   git remote add origin <repo-url>
   git push -u origin main
   ```

3. Set GitHub About metadata:

   ```bash
   gh repo edit <OWNER/REPO> \
     --description "Source-backed SAP context bundles for AI agents, functional design, and field mapping." \
     --add-topic sap \
     --add-topic s4hana \
     --add-topic ai-agents \
     --add-topic functional-design \
     --add-topic field-mapping \
     --add-topic python
   ```

4. Run the full validation gate:

   ```bash
   uv run sap-agent-context validate
   uv run sap-agent-context audit-completeness
   uv run sap-agent-context evaluate-fixtures
   uv run pytest -q
   uv run ruff check .
   ```

5. Create a GitHub release when the first public version is ready.
