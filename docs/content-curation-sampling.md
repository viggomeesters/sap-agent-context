# Content curation sampling protocol

SAP Agent Context uses mechanical repo-level gates, but those gates do not certify
every SAP claim in every domain-pack YAML file. The curation sampling protocol
turns that residual-risk boundary into a repeatable JSON review artifact.

## What it covers

`curation-report` samples claim records from each domain pack and checks whether
the sampled claims carry:

- source/access boundary metadata;
- freshness metadata (`retrieved_at` and `review_after`);
- evidence pointers on the claim;
- explicit fail-closed wording for tenant, client, customizing, configuration or
  assignment-sensitive claims.

It also builds a compact `claim_maturity_index` for every claim, not only the
sampled claims. That index is the next curation surface: fix low maturity claims
or promote selected high-value claims instead of adding more broad coverage.

This complements the repo-level gates for schema validity, runtime retrieval,
source/access boundaries, CI semantics and ontology routing.

## Claim curation maturity

Claim curation maturity is separate from repository or domain maturity. It grades
how safe a single claim is for agent use; it does not certify SAP truth globally.

| Level | Status | Meaning | Next action |
|---|---|---|---|
| `L0` | `blocked` | At least one source/access, freshness, evidence or boundary check fails. | Fix the failed metadata/boundary check before agent use. |
| `L1` | `metadata_ready` | The claim has source/access, freshness, evidence and fail-closed boundary metadata. | Add source specificity, explicit confidence and usage constraints to reach L2. |
| `L2` | `agent_ready` | The claim is fit for clone-local agent use with a specific source posture, explicit medium/high confidence and usage constraints. | Promote only selected high-value claims to L3 with structured expert review evidence. |
| `L3` | `expert_ready` | The claim has explicit high confidence, structured expert review metadata, public exact/catalog evidence and a complete review window. | Keep review windows current; do not generalize beyond the source scope. |

A report can have sampled claims pass while the full maturity index still exposes
`L0` claims. In that case the report status is `needs_curation`: the sample did
not fail, but the complete claim index found blocked claims that should be fixed
before claiming higher curation maturity.

## What it does not claim

The JSON report is not exhaustive claim-by-claim SAP content certification. A
green sample or high L2 count does not prove all SAP claims are accurate for all
products, releases, tenants, localizations or customer variants. Full SAP claim
accuracy curation remains a separate pass.

## Run it

JSON output:

```bash
uv run sap-agent-context curation-report \
  --sample-size 3 \
  --output build/reports/content-curation-sample.json
```

The output JSON contains:

- `summary.maturity_distribution` — total `L0`/`L1`/`L2`/`L3` count across all
  claims;
- `summary.sampled_maturity_distribution` — maturity distribution for the
  deterministic sample;
- `summary.next_maturity_target` — the next curation class to work on;
- `claim_maturity_index` — compact per-claim id, sampled flag, status, level and
  reasons;
- `samples` — full sampled claim evidence, checks and sample-only review decision.

`curation-report` is JSON-only. Markdown in this repo is narrative operating
context for maintainers and agents; generated curation evidence stays
machine-readable JSON.

Convenience target:

```bash
make curation-report
```

## Review decision

Each sampled claim receives one of two review decisions:

- `sample_passed` — the sample has the expected metadata and boundary checks;
- `curation_needed` — at least one sampled check needs a curation/domain review
  pass.

`curation_needed` is not automatically a repository failure. It is a scoped input
for the next content-curation pass. Do not hide it by weakening the sampler.

## When to use

Run a curation sample after:

- large domain-pack additions;
- source/access/freshness policy changes;
- ontology expansions that add many internal-derived claims;
- repo-level audits where the residual risk is “content accuracy, not gate
  semantics”.
