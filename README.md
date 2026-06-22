# SAP FO Knowledge Base

SAP FO Knowledge Base is a curated, link-first knowledge base for generating
source-backed SAP Functional Design context bundles. It stores compact YAML
knowledge items, source pointers, freshness metadata, bundle quality gates, and
deterministic evaluation fixtures for SAP S/4HANA Cloud Public Edition
Functional Design work.

The repository does not mirror SAP Help, SAP Notes, Learning Hub, SAP for Me, or
customer content. It keeps reusable, agent-friendly metadata and cites external
sources through access-labelled pointers.

![SAP FO Knowledge Base hero](assets/hero.svg)

## Highlights

- Canonical YAML knowledge items under `knowledge/**/*.yaml`.
- Rebuildable SQLite, JSONL, and vector-ready indexes under `build/`.
- Context bundle generation through the `sap-fo-kb` CLI.
- Completeness, evidence integrity, retrieval precision, and FO-output
  evaluation gates.
- Typed `sap_fo_context_bundle` contract for downstream consumers such as
  McCoy FO Generator v2.
- Public/gated/internal source labels and review dates to prevent stale or
  private evidence from becoming hidden assumptions.

## Installation

Install `uv` and clone the repository:

```bash
git clone <repo-url>
cd sap-fo-knowledge-base
uv sync
```

For local development without a remote, use the same commands from the repository
root after checking out this folder.

## Usage

Validate the knowledge base:

```bash
uv run sap-fo-kb validate
uv run sap-fo-kb audit-completeness
uv run sap-fo-kb evaluate-fixtures
```

Build indexes:

```bash
uv run sap-fo-kb build-index
```

Generate a context bundle:

```bash
uv run sap-fo-kb query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
```

Create a McCoy local-folder provider manifest:

```bash
uv run sap-fo-kb mccoy-provider \
  build/context-bundles/supplier-invoice-workflow.json \
  --title "SAP FO KB bundle - supplier-invoice workflow" \
  --output build/context-bundles/mccoy-provider.json
```

Representative no-gap queries:

```bash
uv run sap-fo-kb query --intent fo.workflow --topic "supplier-invoice workflow" --sap-product s4hana_cloud_public --limit 12
uv run sap-fo-kb query --intent fo.sap_configuration --topic "procurement purchase requisition workflow" --sap-product s4hana_cloud_public --limit 12
uv run sap-fo-kb query --intent fo.field_mapping --topic "business partner master data" --sap-product s4hana_cloud_public --limit 12
uv run sap-fo-kb query --intent fo.test_scenarios --topic "sales order output management" --sap-product s4hana_cloud_public --limit 12
uv run sap-fo-kb query --intent fo.authorization --topic "integration communication role authorization api" --sap-product s4hana_cloud_public --limit 12
```

## Completeness Scope

The current product-grade scope is `sap_fo_starter_coverage`, defined in
`schema/completeness-matrix.yaml`.

It covers starter Functional Design knowledge for finance/AP, procurement,
sales, master data, migration, workflow, output management, authorizations,
integrations, extensibility, and analytics/reporting. The scope is intentionally
bounded: it is not exhaustive SAP product coverage. It is complete when
`sap-fo-kb audit-completeness` reports zero critical and zero important gaps.

Representative bundles are also checked against the
[Bundle Quality Contract](docs/bundle-quality-contract.md), so completeness is
not only item-count and knowledge-kind coverage.

## Development

Run the full local quality gate:

```bash
uv run sap-fo-kb validate
uv run sap-fo-kb audit-completeness
uv run sap-fo-kb evaluate-fixtures
uv run pytest -q
uv run ruff check .
```

The CI workflow runs the same core validation commands on pushes and pull
requests.

## McCoy Integration

`mccoy-fo-generator-v2` can register generated bundle directories as local
source providers:

```bash
cd /path/to/mccoy-fo-generator-v2
uv run fo-gen-v2 register-source <workspace> <project-id> \
  --type local-folder \
  --title "SAP FO KB bundle - supplier-invoice workflow" \
  --path "/path/to/sap-fo-knowledge-base/build/context-bundles" \
  --provenance sap-fo-knowledge-base
```

Typed consumers should use the
[Typed McCoy Consumer Contract](docs/typed-mccoy-consumer-contract.md). The
local-folder registration path remains backward compatible.

## Privacy And Security

This repository is designed for public release. It stores generic SAP Functional
Design patterns and source pointers, not customer-specific evidence. Do not add
tenant exports, client screenshots, SAP Notes content, credentials, `.env`
files, private keys, personal data, or proprietary customer material.

The `supplier-invoice` filenames are generic SAP process examples, not customer
or private invoice records. See `docs/public-readiness.md` for the current
publication checklist and privacy review notes.

Report security issues privately according to [SECURITY.md](SECURITY.md).

## Release

This Python package is currently source-first. Public releases should be created
as GitHub tags/releases after the repository has a GitHub remote and the quality
gate passes. Until then, the release strategy is documented local validation plus
git commits.

## Remote Strategy

This repository is prepared for a public GitHub source repository, but no remote
is currently configured. Before publishing, create or connect a GitHub
repository and push `main`:

```bash
git remote add origin <repo-url>
git push -u origin main
```

Recommended GitHub metadata:

- Description: `Curated, link-first SAP Functional Design knowledge base for source-backed FO context bundles.`
- Topics: `sap`, `s4hana`, `functional-design`, `knowledge-base`, `python`

## License

MIT License. See [LICENSE](LICENSE).
