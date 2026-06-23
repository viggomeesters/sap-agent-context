# SAP GUI EAM/PM clone-first queries

Run from a fresh clone after `uv sync --locked`.

## Equipment transaction navigation

```bash
uv run sap-agent-context query   --intent fo.navigation   --topic "IE01 IE02 IE03 IH08 /n /o equipment transaction open search"   --sap-product s4hana_cloud_public   --limit 12
```

Expected starter behavior:

- `status: ready`
- includes IE01 create equipment, IE02 change equipment, IE03 display/open equipment, IH08 equipment list/search
- explains `/n` and `/o` as SAP GUI command-field prefixes
- does **not** treat `NIE01` as a standalone transaction code

## IE03 system/user status navigation

```bash
uv run sap-agent-context query   --intent fo.navigation   --topic "Waar zie ik in IE03 gebruiker statussen en systeem statussen equipment"   --sap-product s4hana_cloud_public   --limit 12
```

Expected starter behavior:

- `status: ready`
- includes IE03 display/open equipment context
- includes system status, user status and status profile semantics
- carries tenant-verification caveat for exact screen/menu/status-profile behavior

## System status vs user status

```bash
uv run sap-agent-context query   --intent fo.business_rules   --topic "Wat is het verschil tussen system status en user status status profile"   --sap-product s4hana_cloud_public   --limit 12
```

Expected starter behavior:

- `status: ready`
- explains system status as SAP/system-controlled status context
- explains user status as status-profile/customizing-dependent
- warns not to invent tenant-specific user status values/profile names

## Equipment search / list

```bash
uv run sap-agent-context query   --intent fo.navigation   --topic "Welke transaction gebruik ik om equipment te zoeken IH08 equipment list search"   --sap-product s4hana_cloud_public   --limit 12
```

Expected starter behavior:

- `status: ready`
- includes IH08 equipment list/search context
- keeps exact system availability and authorization caveated

## Public boundary

These examples are public-repo safe. They must not require or include customer data, SAP screenshots, system exports, internal URLs, secrets, proprietary documentation, tenant role/profile names, or real equipment numbers.
