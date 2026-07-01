# SAP Context Ontology

SAP Agent Context should teach an agent to navigate SAP from zero. The repository is not trying to become an exhaustive SAP mirror. It is a source-backed context graph that explains the lenses a consultant uses when deciding whether an SAP claim is generic, release-specific, edition-specific, or tenant-specific.

## Why this exists

A new SAP consultant does not first need every table, Fiori app, API, or SAP Note. They need a mental map:

- what SAP is as an ERP/business process platform;
- where ECC, SAP S/4HANA, S/4HANA Cloud Public Edition, SAP GUI, Fiori, APIs and events fit;
- why implementation phase, system landscape, release, edition and tenant configuration change the answer;
- when SPRO/customizing/CBC/SSCUI evidence is required before a claim is safe;
- how company codes, plants, sales orgs and other org units shape data and process behavior;
- how aliases and generations such as LTMC, Migration Cockpit and Migrate Your Data can point to related but not identical surfaces.

The ontology layer gives agents that map before they consume deeper domain packs.

## The core lenses

| Lens | What it answers | Fail-closed boundary |
|---|---|---|
| Foundation | What is SAP, and what kind of system/context are we talking about? | Do not answer from generic model memory when repo evidence is missing. |
| Lifecycle | Are we before system setup, during Explore/Realize, or running production support? | Do not ask for tenant evidence before a tenant exists; ask for phase-appropriate evidence. |
| Landscape | Is this DEV, QAS, PRD or another system/client? | Do not treat DEV/QAS evidence as production truth. |
| Edition/release | ECC, S/4HANA on-prem/private, S/4HANA Public Cloud, or another edition/release? | Do not collapse old and new surfaces without release/edition caveat. |
| Configuration | Is behavior controlled by SPRO/IMG/CBC/SSCUI/customizing, master data, or code? | Do not claim tenant-specific customizing values generically. |
| Organization | Which org units scope the process/data: company code, plant, sales org, purchasing org, etc.? | Do not validate org-unit values without target-system evidence. |
| Process/capability | Which business process/capability does this belong to? | Do not confuse a process map with implementation-ready configuration. |
| Surface | Is the user interacting through SAP GUI, Fiori app, API/event, report, template or workflow? | Do not infer authorization or availability from a public app/source pointer. |
| Source/evidence | Which public/gated/internal-derived source supports the claim? | Do not copy proprietary SAP docs or SAP Notes text; link and label access/freshness. |

## Navigation rule for agents

Before giving an SAP answer, classify the question through at least these gates:

1. **Surface** — app, transaction, API, table, migration template, workflow, process or concept?
2. **Applicability** — ECC, S/4HANA, Public Cloud, release, lifecycle phase and system landscape?
3. **Tenant dependency** — generic SAP concept, edition/release-specific, or target-tenant customizing/authorization/data?
4. **Evidence** — exact source, gated pointer, internal-derived pattern or missing evidence?
5. **Output stance** — ready answer, caveated answer, or ask for tenant/release/source evidence?

## Organization and process lenses

Organization and process are related, but they prove different things. The
organization lens tells the agent which SAP org units scope the question;
the process lens tells the agent which business flow the question belongs to.
Neither lens proves the target tenant is configured that way.

Core organization lenses:

- **Client / mandant** — system/client partition for customizing and data.
- **Company code** — finance/legal reporting lens; do not collapse it with plant.
- **Controlling area** — management-accounting/control lens; needs assignment evidence.
- **Plant** — logistics, valuation and operations lens.
- **Storage location** — inventory sub-scope under plant context.
- **Sales organization + distribution channel** — O2C/sales-area lens.
- **Purchasing organization** — P2P/procurement responsibility lens.
- **Business partner role** — customer/supplier/process-role semantics.

Core process lenses:

- **O2C** — Order-to-Cash: sales order, delivery, billing, output, customer master.
- **P2P** — Procure-to-Pay: purchase requisition/order, supplier invoice, supplier master.
- **R2R** — Record-to-Report: journals, AP/AR, controlling, financial close.
- **H2R** — Hire-to-Retire: HR/workforce processes; outside current starter depth unless source-backed.
- **D2O** — Design-to-Operate: product, plant, maintenance, production, inventory, quality.

Fail-closed rule: org assignment is tenant/client-specific, a process map is not
configuration proof, and a public SAP concept does not prove the process is
implemented in a customer tenant.

## Examples

- “What is SAP?” should retrieve foundation/context lenses, not only a product list.
- “Where do I configure this?” should retrieve SPRO/customizing/CBC/SSCUI boundaries and ask for target-system evidence where needed.
- “Is this Fiori app available?” should separate public app/library evidence from target business role/catalog and release availability.
- “Can I use LTMC?” should route to alias/evolution/release context before claiming a transaction or tool is current.
- “Can I accept this company code?” should route to org/value-source/customizing evidence, not source-file presence alone.

## Non-goals

- No exhaustive SAP product mirror.
- No copied SAP Help, SAP Notes, Learning Hub or gated text.
- No customer/client/project archive.
- No tenant-specific customizing values.
- No claims that a passing repo gate means “SAP is covered”.
