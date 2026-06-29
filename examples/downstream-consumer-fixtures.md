# Downstream consumer fixture examples

These examples show how an agent should consume `sap-agent-context` bundles without hallucinating missing SAP or tenant facts.

## Example A — ready bundle → cite and draft bounded FO content

Input shape:

```json
{
  "status": "ready",
  "consumer_contract": {
    "name": "sap-agent-context-bundle",
    "version": 1,
    "required_consumer_fields": ["status", "items", "citations", "gaps", "quality_signals"]
  },
  "query": {"intent": "fo.workflow", "topic": "supplier invoice workflow"},
  "citations": [
    {"item_id": "sap.app.manage-workflows-supplier-invoices", "access": "public", "url": "https://example.invalid/sap-help"}
  ],
  "gaps": [],
  "quality_signals": {"gap_count": 0, "stale_count": 0, "expired_count": 0}
}
```

Safe consumer response pattern:

```markdown
Draft-ready starter context for supplier invoice workflow.

Citations:
- `sap.app.manage-workflows-supplier-invoices` — public SAP Help pointer.

FO sections to draft:
- Workflow trigger and approval routing questions.
- Role/authorization impact questions.
- Exception and fallback handling.
- Test scenarios for happy path, rejection, missing approver and authorization failure.

Open questions:
- Confirm tenant workflow variant, approval thresholds and responsible fallback owner.
```

Why this is safe:

- It preserves the citation.
- It says starter context, not customer truth.
- It asks tenant-specific follow-up questions instead of inventing thresholds or approvers.

## Example B — needs-curation bundle → block final output and ask for evidence

Input shape:

```json
{
  "status": "needs_curation",
  "query": {"intent": "fo.reporting", "topic": "generic executive dashboard"},
  "gaps": [
    "Low topic precision; no selected item covers enough of the query tokens."
  ],
  "quality_signals": {"gap_count": 1, "source_url_count": 1}
}
```

Safe consumer response pattern:

```markdown
Draft-only: this bundle is `needs_curation`.

I cannot produce final dashboard requirements from this bundle yet because the selected context is too broad.

Needed before final output:
- target KPI names;
- source query/app/table or analytics artifact;
- filter dimensions and freshness expectation;
- audience/role and authorization boundary.
```

Why this is safe:

- It does not pretend a broad dashboard request is ready.
- It turns the gap into concrete follow-up evidence.
- It avoids invented KPIs, filters, roles or data sources.

## Example C — report_only slice → use as planning signal, not proof

Input shape:

```json
{
  "profile": "analytics_extensibility_candidate",
  "promotion": "report_only",
  "maturity": "deep",
  "note": "Profile is visible for planning but not promoted to required-deep gates."
}
```

Safe consumer response pattern:

```markdown
Planning signal: analytics/extensibility has report-only coverage.

Use it to identify candidate records and gaps, but do not treat it as a final customer-ready slice until the profile is promoted and gates pass.
```

Why this is safe:

- `report_only` is not promoted to final truth.
- It keeps the maturity boundary visible.
- It still gives the agent a useful next-step direction.

## Anti-example — hallucinated tenant fact

Unsafe:

```markdown
The approval threshold is €10,000 and approver role is Z_AP_MANAGER.
```

Why unsafe:

- The bundle did not provide tenant/customer evidence.
- The role name is invented.
- The threshold is invented.

Safe replacement:

```markdown
The bundle does not provide tenant-specific thresholds or role names. Confirm approval thresholds, approver groups and fallback owner in the target tenant before finalizing this FO section.
```
