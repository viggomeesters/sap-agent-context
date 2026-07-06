# SAP Agent Context

SAP Agent Context is a curated, link-first context layer for AI agents working
with SAP functional design, field mapping, workflow, roles, scope items, and
implementation support. It publishes compact JSONL agent records, source
pointers, freshness metadata, bundle quality gates, and deterministic evaluation fixtures
for SAP S/4HANA Cloud Public Edition work.

The repository does not mirror SAP Help, SAP Notes, Learning Hub, SAP for Me, or
customer content. It keeps reusable, agent-friendly metadata and cites external
sources through access-labelled pointers.

![SAP Agent Context hero](assets/hero.svg)

## Highlights

- Canonical JSONL agent records under `records/*.jsonl`.
- Canonical context layout documented in
  [Context Structure](docs/context-structure.md).
- Rebuildable SQLite, FTS5, JSONL, and vector-ready indexes under `build/`.
- Context bundle generation through the `sap-agent-context` CLI.
- Completeness, evidence integrity, retrieval precision, and FO-output
  evaluation gates.
- Typed context bundle contract for downstream consumers such as McCoy FO
  Generator v2 and local AI agent workflows.
- Public/gated/internal source labels, review dates, and expiration dates to
  prevent stale, expired, or private evidence from becoming hidden assumptions.

## Installation

Install `uv` and clone the repository:

```bash
git clone https://github.com/viggomeesters/sap-agent-context.git
cd sap-agent-context
uv sync
```

For local development without a remote, use the same commands from the repository
root after checking out this folder.

## Usage

Validate the context repository:

```bash
uv run sap-agent-context validate
uv run sap-agent-context audit-completeness
uv run sap-agent-context evaluate-fixtures
```

Synchronize legacy authoring files into agent-first JSONL records:

```bash
uv run sap-agent-context export-jsonl --output-dir records
uv run sap-agent-context validate-records --records-dir records
```

The repo is JSONL-first and records-first: `records/*.jsonl` is the canonical agent record
surface. YAML is a legacy authoring/import format kept temporarily for bounded
maintainer curation; it is not the source of truth. The export writes typed JSONL files
for apps, tables, fields, workflows, roles, claims, sources, and relations, then
validates them against `schema/*.schema.json`. The intentional
JSONL-vault-spike alignment and compatibility deviations are documented in
[JSONL record surface](docs/jsonl-record-surface.md). The direct-edit boundary
for agents is documented in
[JSONL migration boundary](docs/jsonl-migration-boundary.md): edit bounded
records or legacy packs, then validate records; do not hand-edit generated
`build/` artifacts or bulk rewrite content to make coverage look complete.

Sample content claims for curation:

```bash
uv run sap-agent-context curation-report --sample-size 3 \
  --output build/reports/content-curation-sample.json
```

The content curation report checks source/access, freshness, evidence and
fail-closed wording on sampled claims, then builds a `claim_maturity_index` for
all claims with L0/L1/L2/L3 curation readiness. It is not exhaustive SAP claim
certification; see [Content curation sampling](docs/content-curation-sampling.md).

Build runtime indexes:

```bash
uv run sap-agent-context build-index
uv run sap-agent-context build-embeddings
uv run sap-agent-context evaluate-runtime-retrieval
uv run sap-agent-context evaluate-semantic-models
uv run sap-agent-context runtime-search "IE03 equipment display" --kind sap_app --vector --limit 5
```

Runtime artifacts under `build/` are generated from canonical `records/*.jsonl`.
SQLite + FTS5 is the primary local agent runtime; sqlite-vec is optional and
local-only. DuckDB is an optional analytics/coverage companion, not the primary
runtime store. See [Local runtime index](docs/local-runtime-index.md) and
[Retrieval trust boundary](docs/retrieval-trust-boundary.md) for what ranked
results can and cannot prove.

Evaluate user-style answer scenarios:

```bash
uv run sap-agent-context evaluate-answer-scenarios
```

This is a deterministic retrieval/evidence-readiness gate. It proves that
representative questions retrieve source-labelled context, required answer terms
and citation-bearing records. It does **not** claim live internet validation,
expert certification, or tenant-specific SAP truth. Fixtures may include public
web evidence hints for a separate human/agent review pass.

| Question | Expected status | Evidence-readiness result |
|---|---:|---|
| `Technical fields in MARA?` | `ready` | retrieves the MARA DD03VT field-catalog anchor and requires `MARA.MATNR`, `MARA.MTART`, `DD03VT` on that record |
| `Field description voor MTART` / `MTART omschrijving` | `ready` | retrieves the MARA field catalog and requires `MARA.MTART`, `Material Type`, `Artikelsoort` |
| `In welke tabellen kan ik het veld MATNR vinden?` / `Welke tabellen hebben MATNR?` | `ready` | retrieves MARA and EQUI field-catalog anchors and requires `MARA.MATNR` plus `EQUI.MATNR` |
| `Hoe zit het precies met organisaties scheiden in SAP?` / `Hoe scheid je organisatie-eenheden in SAP?` | `ready` | retrieves org/process lenses for company code, plant, purchasing organization and sales organization with fail-closed evidence boundaries |
| `Wat is purchase to pay?` / `Wat is procure to pay?` | `ready` | retrieves the P2P/process lens and purchasing-organization context |
| `Welke communicatie arrangement security checks en redactie zijn nodig zonder secrets of tenant URL?` | `ready` | retrieves communication-arrangement security context and keeps tenant URLs, credentials and customer payloads out of public answers |
| `Welke vragen moet ik stellen voor custom field exposure in analytics en API rapportage?` | `ready` | retrieves Custom Fields and Logic / analytical-query context and requires exposure, publish, API/reporting and tenant-availability caveats |
| `procurement release strategy flexible workflow threshold approver evidence` | `ready` | retrieves procurement workflow/control evidence and keeps approver, threshold and customizing behavior tenant-verified |
| `Welke SAP modules zijn er?` | `needs_curation` | retrieves foundation/context lenses, but deliberately refuses to claim an exhaustive module taxonomy from current records |

Example report fragment:

```json
{
  "artifact_kind": "answer_scenario_evaluation_report",
  "status": "passed",
  "fixtures": 14,
  "contract": {
    "live_web_boundary": "Fixtures can carry external evidence hints, but this deterministic gate does not claim live internet validation or expert certification.",
    "answer_boundary": "Retrieved context is answer evidence, not tenant/client-specific SAP configuration proof."
  }
}
```

Example scenario result:

```json
{
  "id": "concrete_mtart_description_paraphrase_nl",
  "question": "MTART omschrijving",
  "expected_answer_status": "ready",
  "status": "passed",
  "top_ids": [
    "sap.field-set.ecc-anonymous-mara-dd03vt-field-catalog"
  ],
  "external_evidence_hints": {
    "mode": "offline_hint",
    "accepted_domains": ["sapdatasheet.org", "se80.co.uk", "sap.com"],
    "search_terms": ["SAP MTART description Material Type", "SAP field MTART Artikelsoort"]
  }
}
```

Generate deterministic consultant-style prose from the same local evidence:

```bash
uv run sap-agent-context consultant-answer "Hoe scheid je organisatie-eenheden in SAP?"
uv run sap-agent-context evaluate-consultant-answers
```

This layer produces a compact answer plus citations and explicit boundaries. It is a narrow deterministic/extractive scenario layer covering material-field, organization/process, integration-security, analytics/extensibility and procurement-workflow intents: no LLM call, no live-web certification, no tenant-specific truth claim, and unsupported/generic questions return `needs_curation` instead of `ready`.

Example answer fragment:

```json
{
  "artifact_kind": "sap_consultant_answer",
  "status": "ready",
  "question": "Hoe scheid je organisatie-eenheden in SAP?",
  "answer": "In SAP, organizational separation should be explained through multiple lenses rather than one magic hierarchy: company code, plant, purchasing organization and sales organization can separate legal, logistics, buying and sales responsibilities...",
  "citations": [
    {
      "id": "sap.field-set.sap-process-lenses",
      "kind": "sap_field",
      "source_ids": ["sap.source.sap-field-set-sap-process-lenses"],
      "claim_ids": ["sap.claim.sap-field-set-sap-process-lenses.001"]
    }
  ],
  "boundary": {
    "live_web_validation": false,
    "expert_certification": false,
    "tenant_specific_truth": false
  }
}
```

Generate a context bundle:

```bash
uv run sap-agent-context query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
```

Create a McCoy local-folder provider manifest:

```bash
uv run sap-agent-context mccoy-provider \
  build/context-bundles/supplier-invoice-workflow.json \
  --title "SAP Agent Context bundle - supplier-invoice workflow" \
  --output build/context-bundles/mccoy-provider.json
```

## Agent Setup

For local AI workflows, each colleague can clone the repository and register the
generated bundle directory with their agent or source-provider layer:

```bash
git clone https://github.com/viggomeesters/sap-agent-context.git sap-agent-context
cd sap-agent-context
uv sync
uv run sap-agent-context query \
  --intent fo.workflow \
  --topic "supplier-invoice workflow" \
  --sap-product s4hana_cloud_public \
  --limit 12 \
  --output build/context-bundles/supplier-invoice-workflow.json
```

The generated bundle includes `producer.name: sap-agent-context` and
`producer.contract: sap-agent-context-bundle`. The legacy
`bundle_kind: sap_fo_context_bundle` remains for backward-compatible consumers.

Representative no-gap queries:

```bash
uv run sap-agent-context query --intent fo.workflow --topic "supplier-invoice workflow" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.sap_configuration --topic "procurement purchase requisition workflow" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.field_mapping --topic "business partner master data" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.test_scenarios --topic "sales order output management" --sap-product s4hana_cloud_public --limit 12
uv run sap-agent-context query --intent fo.authorization --topic "integration communication role authorization api" --sap-product s4hana_cloud_public --limit 12
```

## Completeness Scope

The current product-grade scope is `sap_fo_starter_coverage`, defined in
`schema/completeness-matrix.yaml`.

It covers starter Functional Design knowledge for finance/AP, procurement,
sales, master data, migration, workflow, output management, authorizations,
integrations, extensibility, and analytics/reporting. The scope is intentionally
bounded: it is not exhaustive SAP product coverage. It is complete when
`sap-agent-context audit-completeness` reports zero critical and zero important
gaps.

Representative bundles are also checked against the
[Bundle Quality Contract](docs/bundle-quality-contract.md), so completeness is
not only item-count and knowledge-kind coverage.

For repeatable domain-density work, use the
[Deep domain pack template](docs/deep-domain-pack-template.md) and
`examples/deep-domain-pack-template.yaml`. The template is derived from the
completed EAM/PM lifecycle slice and defines the required source references, FO
patterns, decision rules, tests, fixtures, and bounded thresholds for a named
slice without claiming exhaustive SAP coverage.

The product and design contract is captured in the
[Vision and design principles](docs/vision.json): a cloneable, local-first SAP context runtime for agents that is self-contained, fast, compact, reliable, source-labelled, JSON-first and fail-closed.

## Development

Run the full local quality gate:

```bash
make check
make audit-v02-gap-report
```

`make check` expands to:

```bash
uv run sap-agent-context validate
uv run sap-agent-context audit-completeness
uv run sap-agent-context evaluate-fixtures
uv run sap-agent-context build-index
uv run sap-agent-context build-embeddings
uv run sap-agent-context evaluate-runtime-retrieval
uv run sap-agent-context evaluate-semantic-models
uv run pytest -q
uv run ruff check .
git diff --check
```

`make audit-v02-gap-report` is fail-hard; it must fail the command when the
v0.2 coverage matrix reports blocking findings.

The CI workflow runs `make check` and `make audit-v02-gap-report` on pushes and
pull requests.

## McCoy Integration

`mccoy-fo-generator-v2` can register generated bundle directories as local
source providers:

```bash
cd /path/to/mccoy-fo-generator-v2
uv run fo-gen-v2 register-source <workspace> <project-id> \
  --type local-folder \
  --title "SAP Agent Context bundle - supplier-invoice workflow" \
  --path "/path/to/sap-agent-context/build/context-bundles" \
  --provenance sap-agent-context
```

Typed consumers should use the
[Agent Consumer Contract](docs/agent-consumer-contract.md). McCoy-specific
local-folder registration remains an example integration path in
[McCoy FO Generator v2 Hook Contract](docs/mccoy-fo-generator-v2-hook.md).

## Privacy And Security

This repository is designed for public release. It stores generic SAP context,
Functional Design patterns, field mapping context, and source pointers, not
customer-specific evidence. Do not add tenant exports, client screenshots, SAP
Notes content, credentials, `.env` files, private keys, personal data, or
proprietary customer material.

The `supplier-invoice` filenames are generic SAP process examples, not customer
or private invoice records. See `docs/public-readiness.md` for the current
publication checklist and privacy review notes.

Report security issues privately according to [SECURITY.md](SECURITY.md).

## Release

This Python package is source-first. Public releases should be created as GitHub
tags/releases after the quality gate passes.

## Remote Strategy

Canonical public repository:

```text
https://github.com/viggomeesters/sap-agent-context
```

Recommended GitHub metadata:

- Description: `Source-backed SAP context bundles for AI agents, functional design, and field mapping.`
- Topics: `sap`, `s4hana`, `ai-agents`, `functional-design`, `field-mapping`, `knowledge-base`

## License

MIT License. See [LICENSE](LICENSE).


## SAP GUI EAM/PM examples

- [SAP GUI EAM/PM clone-first queries](examples/sap-gui-eam-pm-queries.json)
