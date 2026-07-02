# SAP Agent Context vision and design principles

## One-line vision

SAP professionals clone `sap-agent-context` as a local, agent-first SAP context
resource: compact enough to run quickly, rich enough to ground useful SAP work,
and strict enough to fail closed when the repo lacks evidence.

## Product promise

A SAP professional should be able to clone this repository, run the local gates,
query it with an agent, and get source-labelled context bundles for SAP
functional design, field mapping, workflow, roles, migration, integrations,
analytics, EAM/PM and implementation support.

The repo is useful when it gives an agent enough structured context to reason
from zero without leaning on generic model memory, while still refusing to invent
release, tenant, customizing, role, availability or production facts.

## North star

> **A cloneable, local-first SAP context runtime for agents: self-contained,
> fast, compact, evidence-backed and fail-closed.**

Every meaningful change should improve at least one part of that sentence. If it
cannot be mapped to the north star, it is probably scope creep.

## Primary user journey

```bash
git clone https://github.com/viggomeesters/sap-agent-context.git
cd sap-agent-context
uv sync --locked
make check
uv run sap-agent-context query-explain --intent fo --topic "maintenance plan task list measuring point" --limit 8
```

Expected outcome:

- the repo builds locally without external hosted retrieval services;
- JSONL records and generated indexes are internally consistent;
- the agent receives compact context, not a documentation dump;
- each useful answer can point to source, freshness and access boundaries;
- missing tenant or release evidence becomes a visible gap, not a hallucinated
  conclusion.

## Design principles

### 1. agent-only product surface

Optimize for agents consuming structured context. Do not design the repo as a
human browsing site, wiki, training manual, or SAP Help replacement.

Allowed narrative docs exist only to preserve operating context for maintainers
and agents. They must not become canonical data, generated evidence, or the main
product surface.

**Good:** JSONL records, bundle contracts, source maps, runtime indexes, fixtures,
query examples, report JSON.

**Bad:** long prose pages that agents must scrape to recover facts that should be
records, claims, sources, relations or fixtures.

### 2. Self-contained local clone

A cloned repo should contain enough source-labelled metadata, schemas, tests and
runtime build commands to be useful on a local machine.

This does not mean copying SAP proprietary documentation. It means carrying
compact, public-safe, link-first records and evidence requirements that let an
agent know what it may say, what it must cite, and what it must ask for.

### 3. Fast by default

Default workflows should complete quickly enough to stay in the development loop.
Heavy or optional work must be explicit.

Design implications:

- keep generated read models rebuildable;
- prefer deterministic JSONL and SQLite/FTS/vector indexes over opaque hosted
  services;
- keep Make targets focused and fail-hard;
- avoid broad content campaigns that slow the gate without improving retrieval or
  evidence.

### 4. Compact, not shallow

Compact means high signal density. It does not mean vague summaries.

A good record is small but useful: id, kind, source, access, freshness, claim,
relations, retrieval hints, caveats and test expectations. A bad record is either
large copied documentation or a shallow label with no evidence boundary.

### 5. Reliable means fail-closed

Reliability is not fluent SAP-sounding output. Reliability is refusing to cross
an evidence boundary.

Fail closed on:

- tenant availability;
- customer/client configuration;
- SPRO/IMG/CBC/SSCUI/customizing values;
- roles and authorizations in a target system;
- release/currentness claims;
- production behavior;
- SAP Notes/KBA/SAP for Me content without authorized verification.

### 6. Evidence before coverage

More domains are not automatically progress. A small source-labelled slice with
fixtures is better than many unverified records.

Promote coverage only when source/access/freshness, runtime retrieval, semantic
fixtures and adversarial cases support the claim.

### 7. JSON-first, generated-artifact JSON-only

`records/*.jsonl` is the canonical agent record surface. Generated report evidence and machine-consumable examples are JSON-only.

Markdown may remain as narrative operating context for maintainers and agents,
but never as generated evidence, report output or machine-readable examples.

### 8. Retrieval is part of the product

A record that cannot be retrieved for the right prompt is not very useful. A
retrieval tweak that breaks nearby domains is not an improvement.

Important behavior needs both:

- positive fixtures/smokes that prove the intended record appears near the top;
- negative fixtures/smokes that prove generic or nearby words do not hijack the
  query.

### 9. Public-safe by construction

The repo must stay cloneable and publishable.

Never store customer names, tenant URLs, screenshots, SAP exports, internal
project identifiers, credentials, proprietary copied SAP documentation, or
customer-specific mappings. Use public/gated/internal-derived access labels and
source pointers instead.

### 10. Every gap should become steerable

A gap is useful when it is named, classified and actionable. Avoid vague backlog
language like “needs more SAP content”.

Prefer generated JSON reports that show:

- affected domain/profile;
- missing source, FO pattern, rule, fixture, freshness or retrieval proof;
- severity or promotion status;
- next curation action.

## What this repo is

| Lens | Meaning |
|---|---|
| Context graph | SAP objects, apps, fields, claims, sources, relations and caveats. |
| Runtime index | Local SQLite/FTS/vector read model generated from records. |
| Evidence layer | Source/access/freshness metadata and proof boundaries. |
| Navigation layer | From-zero SAP lenses: foundation, lifecycle, landscape, edition, release, customizing, org, process, surface and evidence. |
| Agent contract | Bundle schema, query examples, fixtures and fail-closed consumer behavior. |
| Curation system | Reports and tests that turn unknowns into targeted follow-up tasks. |

## What this repo is not

- not a SAP documentation mirror;
- not a Learning Hub clone;
- not a SAP Notes/KBA archive;
- not a customer project archive;
- not a tenant configuration store;
- not a secret store;
- not a generic vector demo;
- not a human wiki as the primary product surface;
- not proof that all SAP claims are globally correct.

## Acceptance scorecard

Use this before merging meaningful changes.

| Question | Pass condition |
|---|---|
| Agent-only | Does the change improve records, bundles, runtime behavior, tests, reports or operating context for agents? |
| Self-contained | Can a fresh clone rebuild or consume the result locally? |
| Fast | Does the default gate stay practical, deterministic and local? |
| Compact | Is the information structured and high-signal rather than copied prose? |
| Reliable | Are source/access/freshness/release/tenant boundaries explicit? |
| JSON-first | Are machine-consumable artifacts JSON/JSONL rather than Markdown? |
| Public-safe | Is there no client, tenant, secret, screenshot, export or proprietary copied text? |
| Retrieval-proof | Are important prompts protected by focused tests, fixtures or query smokes? |
| Gap-steerable | If something is incomplete, is it reported as an actionable gap? |
| No false certainty | Does the output avoid implying exhaustive SAP certification? |

A change that fails one of these checks needs either a fix, a narrower scope, or
an explicit residual risk entry.

## Design review checklist

Before shipping:

1. Does this help SAP professionals clone the repo as a practical agent resource?
2. Is the product surface still agent-first rather than prose-first?
3. Are records/source pointers/freshness/relations explicit where facts matter?
4. Are generated reports and machine examples JSON-only?
5. Are tenant/release/customizing claims fail-closed when target evidence is
   missing?
6. Did the change add retrieval or fixture proof for important behavior?
7. Did full gates pass?
8. Did the final claim state what was proven and what remains outside scope?

## Maturity model

| Level | State | Meaning |
|---|---|---|
| L0 | `schema_valid` | Records parse and validate, but usefulness is not proven. |
| L1 | `retrievable` | Important prompts retrieve the record or bundle. |
| L2 | `source_bounded` | Source/access/freshness and fail-closed caveats are explicit. |
| L3 | `fixture_protected` | Positive and negative tests protect the intended behavior. |
| L4 | `consumer_ready` | Downstream bundle consumers can use it without hidden assumptions. |

Do not call a slice mature because it has many records. Call it mature when it
moves through these levels with evidence.

## Roadmap principles

1. Finish JSONL-native authoring paths without breaking legacy imports.
2. Promote report-only domains only when fixtures and source boundaries justify
   it.
3. Improve `query-explain` until agents can understand why context was selected.
4. Turn curation reports into targeted follow-up tasks.
5. Prefer one deep, verified domain slice over five shallow domains.
6. Keep the repo cloneable, public-safe and local-first even as coverage grows.

## Current residual risk wording

Use this when summarizing audit or gate results:

> Residual risk: audit scope is repo-level, not exhaustive claim-by-claim SAP
> content review across all domain-pack YAML. Gates, runtime behavior,
> source/access boundaries, CI semantics and the from-zero ontology layer are
> covered; full SAP claim curation remains a separate pass.

This wording keeps the repo valuable without pretending that passing gates certify
the entire SAP corpus.
