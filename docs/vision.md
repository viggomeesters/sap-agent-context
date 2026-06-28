# Product vision

`sap-agent-context` should become the local, source-backed SAP context layer that agents can clone, verify, query, and cite when helping with Functional Design, field mapping, test scenarios, workflow, roles, migration, integrations, and implementation support.

It is not a mirror of SAP Help, SAP Notes, Learning Hub, customer systems, or consultant project archives. The project wins when it gives agents enough structured, evidence-labelled context to work faster and safer without pretending to know a tenant or the whole SAP product.

## Target state

A colleague or agent should be able to run:

```bash
git clone https://github.com/viggomeesters/sap-agent-context.git
cd sap-agent-context
uv sync --locked
uv run sap-agent-context export-jsonl --output-dir records
uv run sap-agent-context build-index --sqlite-vec required
uv run sap-agent-context build-embeddings
uv run sap-agent-context query --intent fo --topic "maintenance plan task list measuring point" --limit 12
```

and get a compact context bundle with:

- canonical JSONL agent records;
- source-labelled claims and links;
- bounded freshness and review metadata;
- local SQLite/FTS/vector retrieval;
- FO-ready patterns, questions, assumptions, and non-goals;
- evaluation fixtures that prove important queries still retrieve the right anchors;
- explicit caveats when tenant-specific evidence is required.

## The north star

The north star is:

> **A cloneable, local-first SAP context runtime that turns source-labelled knowledge into verifiable agent context bundles.**

This means the repository should optimize for:

1. **Agent usefulness** — records should answer real agent tasks, not just list SAP terms.
2. **Evidence before fluency** — claims need source labels, freshness, and confidence boundaries.
3. **JSONL-first runtime** — `records/*.jsonl` is the canonical agent record surface; build artifacts are generated.
4. **Local reproducibility** — SQLite, FTS, embeddings, and checks should rebuild from the repo without hosted services.
5. **Bounded density** — a domain can be deep for a named slice without claiming complete SAP coverage.
6. **Fail-closed tenant behavior** — when behavior depends on configuration, roles, status profiles, extensions, settlement, or local process, the answer should ask for evidence instead of inventing detail.

In short: the repo should make **fail-closed tenant behavior** the default for unknown tenant-specific details.

## What “good” looks like

A mature domain slice is not a pile of YAML. It has a complete implementation-pack shape:

| Layer | Good looks like |
|---|---|
| Sources | Public/gated/internal-derived references are labelled, freshness-tagged, and link-first. |
| Anchors | Domain objects, apps, tables, fields, workflow surfaces, roles, and APIs are explicit and citable. |
| FO patterns | Patterns include questions, assumptions, non-goals, and validation notes. |
| Decision rules | Tenant-specific behavior has fail-closed `if/then/outcome` rules. |
| Test patterns | The slice has representative test scenarios and acceptance hints. |
| Retrieval fixtures | Runtime search proves important exact and semantic queries resolve to the right ids. |
| Evaluation fixtures | FO-output and semantic fixtures protect against regression and hallucinated readiness. |
| Density gates | `audit-completeness` reports whether the slice is starter, report-only, or required-deep. |

The completed EAM/PM lifecycle slice is the current exemplar for this shape.

## Boundary

A passing gate means the repo satisfies the stated bounded contract. It is **not exhaustive SAP product coverage**.

## Non-goals

The project should not try to become:

- an exhaustive SAP product knowledge base;
- a copy of SAP proprietary documentation;
- a client/project archive;
- a tenant-specific configuration store;
- a secret store;
- a hosted retrieval service by default;
- a generic vector database demo with weak evidence discipline.

A passing gate means the repo satisfies the stated bounded contract. It does not mean “SAP is covered”.

## Roadmap

### Horizon 1 — Repeat the deep-slice pattern

Goal: prove that EAM/PM was not a one-off.

Recommended next slices:

1. **Analytics and extensibility candidate**
   - Why: it is already visible as a weak/report-only area in the domain-density gates.
   - Output: source anchors, FO patterns, fail-closed rules, fixtures, and a `report_only` profile that can later be promoted.
2. **Integration security and API/event boundaries**
   - Why: high hallucination risk, high reuse value for agents, and strong need for no-secrets policy.
   - Output: safer bundle behavior around communication users, destinations, APIs, events, roles, and no-secret evidence.
3. **Procurement release strategy / workflow caveat slice**
   - Why: common FO topic, but tenant-specific and easy to overclaim.
   - Output: fail-closed patterns and adversarial fixtures that prevent fake-ready workflow guidance.

### Horizon 2 — Make authoring JSONL-native

Goal: reduce legacy YAML authoring friction while preserving compatibility.

Steps:

1. Add a small direct JSONL authoring path for new records.
2. Keep YAML import as a compatibility/editor path, not the canonical source.
3. Strengthen schema tests so record type, SAP context type, source metadata, relations, and freshness are explicit.
4. Preserve deterministic export/build behavior so generated SQLite/FTS/vector indexes remain reproducible.

### Horizon 3 — Improve retrieval trust

Goal: every agent result should explain why it was retrieved.

Steps:

1. Add “why this result?” output to runtime/search/bundle commands.
2. Show exact-token, FTS, vector, source, and fixture evidence separately.
3. Keep exact/source-backed hits ahead of vague vector similarity.
4. Add golden retrieval tests for representative high-risk queries.

### Horizon 4 — Make maturity visible

Goal: make the repo steerable without reading every pack.

Steps:

1. Turn coverage heatmap + domain-density profiles into a maturity dashboard/report.
2. Show each domain as `starter`, `report_only`, or `required-deep`.
3. Show missing dimensions as source, FO, rule, test, retrieval, semantic, or freshness gaps.
4. Generate follow-up task candidates from real gaps, not from broad “more content” impulses.

### Horizon 5 — Harden consumer contracts

Goal: downstream tools can rely on the bundle shape.

Steps:

1. Keep `sap-agent-context-bundle` stable and typed.
2. Maintain compatibility for `sap_fo_context_bundle` only where explicitly needed.
3. Add consumer examples for local agents and McCoy-style FO generation.
4. Keep public/private boundary checks in the default gate.

## Decision rules for future work

Use these rules when deciding what to build next:

1. **Prefer one deep slice over five shallow domains.**
2. **Promote a profile to `required` only after tests prove the slice is deep.**
3. **Add fixtures before trusting retrieval improvements.**
4. **Do not add content without a source, confidence label, or tenant caveat.**
5. **Do not optimize embeddings until exact/source-backed retrieval is protected.**
6. **If a gap is real but out of scope, document it as `later` or create a follow-up task.**
7. **If a proposed change cannot be verified locally, it is not ready for the default gate.**

## Suggested next execution package

The best next execution package is:

> Build the analytics/extensibility slice using the deep-domain pack template.

Acceptance should include:

- a bounded slice name and source registry;
- domain anchors for analytics/reporting/extensibility/custom-field surfaces;
- FO patterns and fail-closed decision rules;
- FO-output, runtime retrieval, and semantic fixtures;
- a `domain_density_profiles` entry that starts as `report_only`;
- tests proving the slice follows the template without weakening existing gates.

This is the cleanest next move because it turns the current known weak area into a repeatable proof that the deep-domain template works beyond EAM/PM.

## Current truth

As of the EAM/PM pass, the repo has:

- JSONL-first records and generated runtime indexes;
- a coverage heatmap;
- EAM/PM lifecycle deep-slice content;
- FO patterns and decision rules for that slice;
- FO-output, runtime retrieval, and semantic fixtures;
- bounded domain-density gates;
- a reusable deep-domain pack template.

The project is ready to shift from “prove the architecture once” to “repeat the pattern deliberately”.
