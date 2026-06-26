# Local runtime index

SAP Agent Context uses an agent-first storage split:

1. `records/*.jsonl` is the canonical agent record surface for applications,
   tables, fields, workflows, roles, claims, sources, and relations.
2. `build/context.sqlite`, `build/items.jsonl`, and `build/vector-corpus.jsonl`
   are generated runtime artifacts. Rebuild them; do not hand-edit them.
3. YAML knowledge files remain the migration/editing source until the JSONL
   record surface is explicitly promoted as the only edit surface.

## Rebuild

```bash
uv run sap-agent-context validate
uv run sap-agent-context export-jsonl --output-dir records
uv run sap-agent-context build-index
uv run sap-agent-context build-embeddings
uv run sap-agent-context evaluate-runtime-retrieval
uv run sap-agent-context evaluate-semantic-models
```

`build-index` reads `records/*.jsonl` when present. If records are missing, it
exports temporary records from YAML first for backward compatibility.

## Runtime layers

| Layer | Purpose | Canonical? |
| --- | --- | --- |
| `records/*.jsonl` | typed item/claim/source/relation records | yes |
| `build/context.sqlite` | local agent query store: items, claims, sources, relations, FTS5; includes `read_model_metadata` marking it generated/non-authoritative | no |
| `build/vector-corpus.jsonl` | deterministic text chunks for local embedding | no |
| `vector_embedding_records` / `vector_embeddings` | FastEmbed + sqlite-vec semantic vectors | no |
| `vector_index_metadata` | generated vector build status/model/dimension/source metadata | no |

SQLite + FTS5 is the primary local runtime. `sqlite-vec` is included as a
local-only dependency and `build-index --sqlite-vec required` must succeed in a
fresh clone after `uv sync`. The semantic layer uses FastEmbed with
`BAAI/bge-small-en-v1.5` by default, writes 384-dimensional embeddings into
sqlite-vec, and records provider/model/dimension/vector count in
`vector_index_metadata`.

DuckDB can be useful for analytics, coverage checks, and embedding-quality
analysis over JSONL, but it is not the primary runtime store for agent lookup.

## Local embedding setup

The repository does not introduce Pinecone or another cloud vector dependency.
Local embedding providers should be configured from
`schema/runtime-embedding-config.schema.json`, currently allowing:

- `fastembed`
- `sentence-transformers`
- `ollama`
- `custom-local`

The generated vector corpus uses stable IDs:

- item chunks: `<canonical item id>#summary`
- claim chunks: `<canonical claim id>#statement`

Vector rows must preserve `canonical_record_id`, source/citation metadata, and a
stable content hash strategy so caches can be rebuilt safely.

`evaluate-semantic-models` runs local NL/EN semantic fixtures against one or
more FastEmbed models. `BAAI/bge-small-en-v1.5` remains the default unless this
local eval evidence shows a larger local model is needed. Do not add cloud
embedding providers or hosted vector services for this repo.

## Query examples

Exact SAP code lookup:

```bash
uv run sap-agent-context build-index
uv run sap-agent-context build-embeddings
uv run sap-agent-context runtime-search "IE03 equipment display" \
  --kind sap_app \
  --vector \
  --limit 5
```

Table/field lookup:

```bash
uv run sap-agent-context runtime-search "EQUI equipment table" --limit 8
uv run sap-agent-context runtime-search "DD03VT field catalog" --limit 8
```

Natural-language lookup:

```bash
uv run sap-agent-context runtime-search \
  "How do I display equipment master data?" \
  --limit 8
```

Retrieval gate:

```bash
uv run sap-agent-context evaluate-runtime-retrieval
```

The runtime-search output includes item IDs, claim IDs, source/evidence IDs,
exact-token hits, and score fields. That shape is intended to be consumable by
bundle generation while keeping the existing `sap_fo_context_bundle` output
backward compatible.

## Public boundary

This repository is public-safe only when it stays generic and source-backed.
Do not add customer data, tenant exports, screenshots from SAP systems, internal
URLs, credentials, `.env` files, private keys, SAP Notes text, copied proprietary
SAP documentation, or client/project identifiers. Do not add customer data,
internal URLs, or copied proprietary SAP documentation. Public or gated source
pointers are fine; copied source text is not.
