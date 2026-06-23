# Public Readiness

SAP Agent Context is a professional public GitHub project for source-backed SAP
context bundles that AI agents can clone, validate, query, and register as a
local context/source layer.

## Current Status

- Public remote is configured: `https://github.com/viggomeesters/sap-agent-context.git`.
- Source code, tests, documentation, license, security policy, contribution
  guide, changelog, CI workflow, and repository visual assets are present.
- Full local quality gate passes: repository guard, validation, completeness
  audit, evaluation fixtures, pytest, Ruff, and whitespace diff check.
- Generated indexes, context bundles, SQLite files, JSONL exports, and provider
  manifests belong under `build/` and are rebuildable outputs, not canonical
  source material.
- Releases are explicit-only: no tag or GitHub release should be created without
  a fresh release decision.

## Privacy Review Notes

This repository is designed for public release. It stores generic SAP context,
source pointers, freshness/access labels, synthetic examples, and internal-derived
implementation patterns. It must not store customer-specific evidence.

Automated filename checks may flag paths containing `supplier-invoice`. In this
repository those files are generic SAP process examples used for Functional
Design bundle tests. They are not real supplier invoices, customer records,
screenshots, or proprietary client artifacts.

Field Atlas material is public-safe only after source review. Absorbed context is
stored as link-first public pointers or labelled internal-derived generic patterns;
review-pending external dictionaries are not bulk-imported.

Before publishing a release, run a final manual review for:

- credentials, `.env` files, API keys, private keys, and tokens;
- customer-specific SAP tenant data, URLs, hostnames, exports, screenshots, or
  real document attachments;
- copied SAP Help, SAP Notes, Learning Hub, SAP for Me, or proprietary customer
  content;
- private names, project IDs, tickets, implementation data, or client-specific
  mappings.

## Clone-first Smoke

A colleague should be able to clone and run:

```bash
git clone https://github.com/viggomeesters/sap-agent-context.git
cd sap-agent-context
uv sync --locked
make check
uv run sap-agent-context query \
  --intent fo.workflow \
  --topic "supplier invoice approval payment block payment proposal" \
  --sap-product s4hana_cloud_public \
  --limit 12
uv run sap-agent-context query \
  --intent fo.integration \
  --topic "integration api communication arrangement credentials tenant url payload business key error handling no secrets" \
  --sap-product s4hana_cloud_public \
  --limit 12
```

Expected result: both focused queries return `bundle_kind: sap_fo_context_bundle`
and `status: ready`; broad/generic probes may return `needs_curation` by design.

## GitHub Metadata

Recommended About metadata:

- Description: `Source-backed SAP context bundles for AI agents, functional design, and field mapping.`
- Topics: `sap`, `s4hana`, `ai-agents`, `functional-design`, `field-mapping`, `knowledge-base`, `python`

Optional command:

```bash
gh repo edit viggomeesters/sap-agent-context \
  --description "Source-backed SAP context bundles for AI agents, functional design, and field mapping." \
  --add-topic sap \
  --add-topic s4hana \
  --add-topic ai-agents \
  --add-topic functional-design \
  --add-topic field-mapping \
  --add-topic knowledge-base \
  --add-topic python
```

## Release Checklist

1. Confirm `main` is clean and pushed.
2. Run the full validation gate:

   ```bash
   make check
   ```

3. Run at least one clone-first query and one negative/generic query:

   ```bash
   uv run sap-agent-context query --intent fo.workflow --topic "supplier invoice approval payment block payment proposal" --sap-product s4hana_cloud_public --limit 12
   uv run sap-agent-context query --intent fo.analytics --topic "generic executive dashboard performance report" --sap-product s4hana_cloud_public --limit 12
   ```

4. Re-read this privacy checklist and inspect `git status --short --branch`.
5. Only then create a tag/GitHub release if a release is explicitly authorized.

## Known Public-Readiness Risks

- GitHub About metadata and topics may drift; verify them via `gh repo view` or
  the GitHub UI before announcing the repository.
- Generic `supplier-invoice` filenames are intentional SAP process examples, but
  release reviewers should still treat filename-based privacy scanners as a
  manual review signal.
- `build/` outputs are generated and should not be committed as canonical source.
