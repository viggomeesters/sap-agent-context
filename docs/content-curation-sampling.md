# Content curation sampling protocol

SAP Agent Context uses mechanical repo-level gates, but those gates do not certify
every SAP claim in every domain-pack YAML file. The curation sampling protocol
turns that residual-risk boundary into a repeatable review artifact.

## What it covers

`curation-report` samples claim records from each domain pack and checks whether
the sampled claims carry:

- source/access boundary metadata;
- freshness metadata (`retrieved_at` and `review_after`);
- evidence pointers on the claim;
- explicit fail-closed wording for tenant, client, customizing, configuration or
  assignment-sensitive claims.

This complements the repo-level gates for schema validity, runtime retrieval,
source/access boundaries, CI semantics and ontology routing.

## What it does not claim

The JSON report is not exhaustive claim-by-claim SAP content certification. A
green or low-issue sample does not prove all SAP claims are accurate for all
products, releases, tenants, localizations or customer variants. Full SAP claim
accuracy curation remains a separate pass.

## Run it

JSON output:

```bash
uv run sap-agent-context curation-report \
  --sample-size 3 \
  --output build/reports/content-curation-sample.json
```

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
