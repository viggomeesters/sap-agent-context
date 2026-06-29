# Deep-slice retro gate

`schema/deep-slice-retro-gate.yaml` records the reusable retro checklist for bounded SAP deep slices.

The gate compares completed slices against the dimensions in `examples/deep-domain-pack-template.yaml` and `docs/deep-domain-pack-template.md`:

- source references
- domain anchors
- FO patterns
- fail-closed decision rules
- test patterns
- FO-output fixtures
- runtime retrieval fixtures
- semantic fixtures
- density profile or explicit no-follow-up reason

## Current retro result

Checked slices:

| Slice | Status | Follow-up disposition |
|---|---|---|
| `eam_pm_lifecycle` | exemplar | none |
| `analytics_extensibility` | checked | no follow-up; report-only slice remains bounded |
| `integration_security` | checked | no follow-up; runtime stays app/policy anchored while FO/semantic gates cover deep rules |
| `procurement_release_strategy` | checked | no follow-up; generic release-strategy query remains adversarial `needs_curation` |

This satisfies the immediate retro gate because at least two non-EAM slices are checked, each template dimension has a disposition, and concrete gaps have either a follow-up path or an explicit no-follow-up reason.

## Guardrail

A retro pass is **not exhaustive SAP coverage**. It only says the named slice has enough bounded evidence and tests for the current campaign stage.
