# Public Readiness

SAP Agent Context is intended to be published as a professional public GitHub
project after a remote is connected.

## Current Status

- Source code, tests, documentation, license, security policy, contribution
  guide, changelog, CI workflow, and repository visual assets are present.
- No `.env`, private key, token, private screenshot, customer export, or large
  binary artifact is stored in the current repository files.
- Generated indexes, context bundles, SQLite files, JSONL exports, and provider
  manifests belong under `build/` and are rebuildable outputs, not canonical
  source material.
- No GitHub remote is configured yet, so GitHub visibility, About metadata,
  topics, and releases cannot be verified locally.

## Privacy Review Notes

Automated filename checks may flag paths containing `supplier-invoice`. In this
repository those files are generic SAP process examples used for Functional
Design bundle tests. They are not real supplier invoices, customer records,
screenshots, or proprietary client artifacts.

Field atlas material is public-safe only after source review. The reviewed
starter item `sap.field-set.supplier-invoice-routing` is internal-derived,
generic implementation context. The larger Excel dictionaries in sibling
repositories are review-pending sources and have not been bulk-imported.

Git history currently contains the same `supplier-invoice` example filenames
because those examples were added in earlier commits. Treat the history finding
as a manual review item before publishing. Do not rewrite history unless the
manual review finds real private data.

Before publishing, run a final manual review for:

- credentials, `.env` files, API keys, private keys, and tokens;
- customer-specific SAP tenant data;
- copied SAP Help, SAP Notes, Learning Hub, or SAP for Me content;
- private screenshots or binary attachments;
- proprietary client names or implementation data.

## Publish Checklist

1. Create a public GitHub repository named `sap-agent-context`.
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

## Known External Blockers

- GitHub remote, public visibility, description, and topics cannot be verified
  until a remote exists.
- Repo-complete filename and git-history heuristics flag generic
  `supplier-invoice` paths. Manual review is required before publishing; current
  file contents are generic examples, not private invoice records.
- A first GitHub release is optional, but the release decision should be made
  after the remote is connected and the full validation gate passes.
