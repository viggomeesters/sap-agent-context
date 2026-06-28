# Deep domain pack template

Use this template when a new SAP domain slice needs to move from starter context to bounded implementation-pack coverage in `sap-agent-context`.

The completed EAM/PM lifecycle slice is the exemplar. It proved one repeatable pattern:

1. add source-labelled domain anchors;
2. add FO-useful patterns and fail-closed decision rules;
3. add test-pattern, FO-output, runtime retrieval, and semantic fixtures;
4. add bounded domain-density thresholds;
5. verify the slice without claiming exhaustive SAP coverage.

Template file:

```text
examples/deep-domain-pack-template.yaml
```

## What this template proves

A domain that follows this template can claim:

> bounded implementation-pack coverage for a named slice.

It must not claim:

> exhaustive SAP product coverage, full module coverage, or tenant-specific behavior without tenant evidence.

In short: a passing template is **not exhaustive SAP product coverage**.

## Required dimensions

| Dimension | Required proof | EAM/PM exemplar |
|---|---|---|
| Source references | Link-first public/gated/internal-derived anchors with freshness and license notes | `sap.ref.eam.pm.sap-help-task-list-display` |
| Domain anchors | `sap_object` and `sap_app` records that patterns/rules can cite | maintenance plan, task list, measuring point, work center |
| FO patterns | questions, assumptions, non-goals, validation notes | `sap.pattern.eam.pm-task-list-plan-fo` |
| Decision rules | fail-closed `if/then/outcome` rules | `sap.rule.eam.pm-task-list-plan-tenant-questions` |
| Test patterns | FO/test-scenario anchors tied to the slice | EAM lifecycle test-pattern records |
| FO eval fixtures | `schema/fo-output-evaluation-fixtures.yaml` entries with expected ids | task-list/plan and counter probes |
| Runtime fixtures | `schema/runtime-retrieval-fixtures.yaml` entries with expected ids | IP10/IA03/IK03/TECO settlement probes |
| Semantic fixtures | `schema/semantic-model-fixtures.yaml` entries for vocabulary/locale recall | NL/EN EAM probes |
| Density profile | `schema/completeness-matrix.yaml` `domain_density_profiles` entry | `eam_pm_lifecycle` |

## Promotion policy

Start every new domain-density profile as:

```yaml
promotion: report_only
```

Missing dimensions then appear as `later` findings in `audit-completeness` and do not break starter coverage.

Promote to:

```yaml
promotion: required
```

only after the slice meets its bounded thresholds and has tests proving the profile is `deep`. Missing required dimensions then become `important` findings and fail `audit-completeness`.

## Workflow for a new domain slice

1. Copy `examples/deep-domain-pack-template.yaml` as a design checklist.
2. Create or update one bounded pack under `knowledge/domain-packs/`.
3. Keep the source registry link-first; do not copy proprietary SAP docs.
4. Add FO patterns with required questions, assumptions, non-goals and validation notes.
5. Add fail-closed decision rules for tenant-specific behavior.
6. Add FO-output, runtime retrieval and semantic fixtures.
7. Add a `domain_density_profiles` entry in `schema/completeness-matrix.yaml` with `promotion: report_only`.
8. Add focused tests for the new slice.
9. Run:

```bash
uv sync --locked
make check
git diff --check
```

## Guardrails

- Do not create broad SAP filler to satisfy item counts.
- Do not use `required` promotion as a promise that the whole SAP domain is complete.
- Do not invent tenant-specific status codes, workflows, roles, table fields, settlement behavior, authorizations or app availability.
- Do not mix public pointers with private/customer evidence.
- If a missing dimension is real but out of scope, create a follow-up task or leave the profile `report_only` with a documented `later` finding.
