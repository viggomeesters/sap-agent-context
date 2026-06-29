# Next-slice prioritization heuristic

Use this when choosing the next bounded SAP slice after EAM/PM. The goal is not to add broad SAP filler; the goal is to pick slices where structured records materially improve FO/retrieval safety and can be proven with local gates.

## Inputs

Run these signals before deciding:

```bash
uv run sap-agent-context maturity-report
uv run sap-agent-context gap-report
uv run sap-agent-context audit-completeness
uv run sap-agent-context evaluate-runtime-retrieval
```

Use the outputs as planning evidence, not as SAP truth percentages.

## Scoring

Score each candidate slice from 0–2 on each dimension:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Maturity gap | No concrete missing dimension | Some missing evidence or weak profile | Required/report_only gap blocks useful output |
| Retrieval value | Rarely asked / low reuse | Useful in one workflow | Reusable across FO, tests, roles, data, integration or migration |
| FO risk | Low tenant variance | Some tenant/config variance | High hallucination risk without fail-closed rules |
| Source availability | No safe source route | Internal-derived only or gated | Public/gated/internal sources can be labeled safely |
| Fixtureability | Hard to verify deterministically | One fixture class available | Runtime + FO-output + semantic/adversarial fixtures are feasible |
| Non-filler specificity | Broad module bucket | Named scenario but still fuzzy | Narrow slice with concrete apps/objects/rules/questions |

Default ranking:

```text
priority = maturity_gap + retrieval_value + fo_risk + source_availability + fixtureability + non_filler_specificity
```

Tie-breakers:

1. prefer slices that reduce fake-ready tenant-specific guidance;
2. prefer slices already visible in `gap-report` or `domain_density_profiles`;
3. prefer slices with source-backed fixtures available now;
4. avoid slices that only increase item counts without better FO patterns/rules/tests.

## Candidate example

| Candidate slice | Gap signal | Retrieval value | FO risk | Source availability | Fixtureability | Non-filler specificity | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Analytics/extensibility candidate | 1 | 2 | 2 | 2 | 2 | 2 | 11 | Highest: report_only profile already exists and custom-field/reporting output is high-risk. |
| Integration security/API boundaries | 1 | 2 | 2 | 2 | 2 | 2 | 11 | Co-highest: no-secrets and communication-arrangement caveats protect many consumers. |
| Procurement release strategy/workflow caveat | 1 | 2 | 2 | 1 | 2 | 2 | 10 | Strong next slice when workflow/approval source anchors are enough. |
| Generic executive dashboard | 0 | 1 | 1 | 1 | 1 | 0 | 4 | Do not choose: too broad; current gates correctly treat it as curation/generic. |
| Whole SAP Finance module | 0 | 2 | 2 | 1 | 0 | 0 | 5 | Do not choose as stated: split into a named sub-slice first. |

## Decision rule

Pick a candidate only if all are true:

- it has a narrow name: object/app/process/rule/testable question, not a whole module;
- follow-up work can produce at least one source reference, one anchor, one FO pattern, one decision rule and one fixture;
- the expected output improves retrieval or FO safety, not just coverage counts;
- the slice can stay `report_only` until it meets the deep-domain template;
- no customer/tenant/private evidence is needed to make public-safe progress.

If a candidate fails any condition, record an explicit no-follow-up reason and pick the next candidate.

## Recommended next move

Start with either:

1. **Analytics/extensibility candidate** — because it already exists as `report_only`, has high consumer value, and custom-field/reporting provenance is easy to overclaim.
2. **Integration security/API boundaries** — because source/access/no-secrets boundaries are broadly reusable and high-risk.

Keep procurement release strategy/workflow as the third candidate unless a concrete FO use-case makes it more urgent.

## Guardrails

- Do not pick broad SAP filler as progress.
- Do not promote `report_only` to `required` until all deep-domain dimensions and fixtures pass.
- Do not invent tenant-specific fields, roles, workflows, thresholds, statuses or API behavior.
- Do not treat maturity score as a business truth percentage.
- Materialize follow-up tasks for the chosen slice; otherwise record why no follow-up is created.
