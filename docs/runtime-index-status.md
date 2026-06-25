# Runtime index status

Verified on: 2026-06-25

## Status summary

SAP Agent Context now matches the clone-first design principle for a local agent
context repository:

```text
git clone -> uv sync -> export JSONL -> build SQLite/FTS/vector corpus -> build FastEmbed vectors -> query with evidence
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
| Embedding vectors | ready | FastEmbed `BAAI/bge-small-en-v1.5`, 384 dimensions, 1,289 sqlite-vec rows |
| Retrieval evals | ready | 5 runtime retrieval fixtures passed |
| Repo public boundary | ready | no generated `build/` artifacts tracked; no customer data/secrets required |

## Runtime commands

```bash
uv sync
uv run sap-agent-context validate
uv run sap-agent-context export-jsonl --output-dir records
uv run sap-agent-context build-index --sqlite-vec required
uv run sap-agent-context build-embeddings --provider fastembed --model BAAI/bge-small-en-v1.5
uv run sap-agent-context evaluate-runtime-retrieval
uv run sap-agent-context runtime-search "IE03 equipment display" --kind sap_app --vector --limit 5
```

## Design principle check

- **Cloneable**: yes. Runtime is generated locally from tracked source files and
  tracked JSONL records.
- **Fast retrieval**: yes for exact/token retrieval through SQLite + FTS5 and
  deterministic reranking. Exact SAP identifiers such as `IE03`, `EQUI`, and
  `DD03VT` are covered by runtime eval fixtures.
- **Evidence-backed**: yes. Runtime search returns item IDs plus claim/source
  IDs, and SQLite stores first-class claims, sources, and relations.
- **Vector retrieval**: yes. FastEmbed `BAAI/bge-small-en-v1.5` builds local
  384-dimensional embeddings into sqlite-vec from `build/vector-corpus.jsonl`.
  Runtime search can opt into `--vector` while FTS5/evidence ranking remains the
  primary safety rail.
- **Public-safe**: yes by design. The repo stores generic SAP context, source
  pointers, and consultant-derived claims; it must not contain customer data,
  tenant exports, internal URLs, copied proprietary SAP docs, or secrets.

## Current boundary

The semantic embedding layer is now local and concrete, but still intentionally
bounded. It uses a small default model for clone-first CPU usage. If NL/EN
cross-lingual recall proves weak, the next decision is an eval-backed comparison
against `BAAI/bge-m3`, not a cloud vector service.

Generated runtime artifacts remain rebuildable and untracked; `records/*.jsonl`
stays the canonical agent record surface.
