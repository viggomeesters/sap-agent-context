# Material + ETM starter scope

This scope extends SAP Agent Context with a bounded Material + ETM starter slice.
It is public-repo safe and does not claim exhaustive SAP product coverage.

## In scope

### Material / Product Master

Starter coverage should let agents answer clone-first consultant questions about:

- material/product master identity and source pointers;
- material type / product type caveats;
- plant-specific data: purchasing, MRP, valuation/accounting and storage-location context;
- sales/distribution usage where relevant;
- batch and serial number caveats;
- stock/availability queries such as MMBE-style starter navigation;
- SAP GUI starter transactions such as MM01, MM02, MM03, MM60 and MMBE, where represented as internal-derived navigation context with caveats.

### EAM material links

Starter coverage should connect material context to EAM/PM questions about:

- spare parts and material components;
- equipment or functional-location BOM context;
- maintenance order component planning/consumption;
- material availability caveats for maintenance execution;
- serial/batch-managed spare-part caveats.

### ETM

ETM is ambiguous. In this repo, ETM may only be answered as **Equipment and Tools Management / EAM-adjacent context** when the item is backed by a public/gated pointer or explicitly labelled `internal_derived` with confidence and tenant-verification caveats.

Do not use ETM as a magic universal SAP module label. If a query asks for a different ETM meaning, the bundle should either fail closed or state that the acronym needs clarification.

## Out of scope for this starter loop

- exhaustive MM/IM/PP/EWM/WM product coverage;
- exact tenant configuration, material types, valuation classes, stock statuses or status/profile names;
- customer equipment/material numbers;
- screenshots, SAP exports, internal URLs or proprietary SAP documentation text;
- copied SAP documentation.

## Source strategy

Use link-first public/gated pointers and compact claims:

- SAP Learning / SAP Help / SAP API catalog URLs are pointers, not copied text;
- consultant knowledge is allowed only as `internal_derived` with confidence and tenant verification caveats;
- exact field, view, configuration and transaction behavior must be verified in the target tenant/system before implementation use.

## Representative queries for final hardening

- `MM01 MM02 MM03 MM60 MMBE material master product SAP GUI /n`
- `material master plant storage location valuation MRP purchasing sales views`
- `spare parts material component equipment BOM maintenance order`
- `ETM equipment tools management material equipment EAM caveat`
- `NMM03 /nMM03 material transaction prefix`
