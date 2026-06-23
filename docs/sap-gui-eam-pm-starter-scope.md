# SAP GUI EAM/PM starter coverage scope

This scope defines what "complete" means for the first SAP GUI EAM/PM fill loop in this public repository.

## In scope

Starter coverage is limited to SAP GUI consultant questions about Equipment / EAM / Plant Maintenance:

- `IE01` create equipment.
- `IE02` change equipment.
- `IE03` display/open equipment.
- `IH08` equipment list/search.
- SAP GUI command-field prefixes `/n` and `/o` as navigation prefixes, not new transaction codes.
- Where a consultant should look for system status and user status context around equipment display/change.
- Difference between system status, user status, status profile, and tenant-specific verification caveats.

## Out of scope

This scope is not exhaustive SAP EAM/PM coverage. It does not claim full SAP product documentation for:

- notifications, maintenance plans, task lists, measuring points, counters, BOMs, work centers or settlement;
- tenant-specific screen layouts, authorization objects, user statuses, status profile configuration or field selection;
- copied SAP documentation, screenshots, customer exports or project-specific navigation.

## Source and confidence policy

Allowed context must be one of:

- `public` or `gated` link-first source pointer with access and freshness labels;
- `internal_derived` consultant knowledge with explicit confidence and tenant-verification caveat.

All public-ready answers must preserve this distinction. If a query cannot be answered without tenant-specific verification, the bundle must carry a caveat or fail closed.
