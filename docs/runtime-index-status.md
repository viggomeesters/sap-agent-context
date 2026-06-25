# Runtime index status

Verified on: 2026-06-25

## Status summary

SAP Agent Context now matches the clone-first design principle for a local agent
context repository:

```text
git clone -> uv sync -> export JSONL -> build SQLite/FTS/vector corpus -> query with evidence
```

A colleague's agent can clone the repo, run the local commands below, and query a
large SAP sub-context without a hosted vector service, private account, or
customer data dump.

## Verified live state

| Surface | Status | Evidence |
| --- | --- | --- |
| Canonical JSONL | ready | `records/*.jsonl`, 8 files, 2,882 records |
| SQLite runtime | ready | `build/context.sqlite`, generated from `records/*.jsonl` |
| FTS5 | ready | `item_fts`, `claim_fts`, `source_fts` tables present |
| Evidence tables | ready | `claims=658`, `sources=631`, `relations=962` |
| Vector corpus | ready | `build/vector-corpus.jsonl`, 1,289 item/claim chunks |
| sqlite-vec dependency | ready | `sqlite-vec` is a project dependency; `--sqlite-vec required` succeeds |
| Embedding vectors | not configured | provider/model/dimension intentionally `not-configured` until a local embedding provider is selected |
| Retrieval evals | ready | 5 runtime retrieval fixtures passed |
| Repo public boundary | ready | no generated `build/` artifacts tracked; no customer data/secrets required |

## Runtime commands

```bash
uv sync
uv run sap-agent-context validate
uv run sap-agent-context export-jsonl --output-dir records
uv run sap-agent-context build-index --sqlite-vec required
uv run sap-agent-context evaluate-runtime-retrieval
uv run sap-agent-context runtime-search "IE03 equipment display" --kind sap_app --limit 5
```

## Design principle check

- **Cloneable**: yes. Runtime is generated locally from tracked source files and
  tracked JSONL records.
- **Fast retrieval**: yes for exact/token retrieval through SQLite + FTS5 and
  deterministic reranking. Exact SAP identifiers such as `IE03`, `EQUI`, and
  `DD03VT` are covered by runtime eval fixtures.
- **Evidence-backed**: yes. Runtime search returns item IDs plus claim/source
  IDs, and SQLite stores first-class claims, sources, and relations.
- **Vector-ready**: yes. Vector corpus and sqlite-vec dependency are present.
  Actual embeddings are intentionally the next configurable layer, not hardcoded
  into the repository.
- **Public-safe**: yes by design. The repo stores generic SAP context, source
  pointers, and consultant-derived claims; it must not contain customer data,
  tenant exports, internal URLs, copied proprietary SAP docs, or secrets.

## Current boundary

This is not yet a full semantic embedding system. The repo is ready to add a
local embedding provider (`fastembed`, `sentence-transformers`, `ollama`, or
`custom-local`) against `build/vector-corpus.jsonl`, but the current shipped
runtime is SQLite + FTS5 + evidence-first hybrid retrieval.

That boundary is intentional: keep `records/*.jsonl` canonical, keep generated
runtime artifacts rebuildable, and avoid hardcoding a cloud vector dependency.
