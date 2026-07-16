# Station Control Center (SCC) — JLG Jefferson City
# CLAUDE.md — Full project context for Claude Code sessions

## What this project is

The Station Control Center is an Ignition Perspective tool inside the **FactoryControl** project
at JLG Industries, Jefferson City TN. It lets authorized users (Engineering, Supervisor, Scheduler)
perform the most common Station Control manual interventions without opening the Ignition Designer.
Every committed action writes to the existing SupervisorOverrideLog table.

Developer: MDI (embedded JLG resource)

---

## Absolute rules (non-negotiable, established through build review)

1. **No polling bindings.** Every query binding must have `polling.enabled = false`. Data
   refreshes on demand (button click / selection / after commit). No timer scripts. No
   tag-change scripts. No per-row tag subscriptions. Gateway memory and flood limits.

2. **Real Perspective event names only.** `ia.display.table` fires `onSelectionChange` —
   NOT `onRowClick`. `onRowClick` does not exist and silently never fires. The lint in
   `sim.py` enforces this. Do not use `onRowClick` anywhere.

3. **No theme tokens.** `--textPrimary`, `--container`, `--containerRoot`, `--accent-primary`,
   etc. are NOT defined in this project. Using them makes labels invisible. Use concrete hex
   only: `#1B212B` (text), `#FFFFFF` (card bg), `#F4F6F9` (page bg), `#D8DEE7` (border),
   `#E87722` (JLG orange), `#5B6675` (muted text), `#2F9E44` (green), `#E8920C` (warn),
   `#E03131` (error).

4. **No dark mode, no theme toggle.** `session.props.theme` is not a real property in this
   project. Remove any toggle or theme-switching code entirely.

5. **Real script namespace only.** The script library lives at `StationControl/SCC/code.py`
   inside the **existing** `StationControl` package. Calls are `StationControl.SCC.<fn>`.
   `StationControlCenter` does not exist as a namespace. Do not invent new top-level packages.

6. **No PLC status gating.** The SCC does not read PLC status anywhere. The only status
   that matters for the Station ComponentID boundary check is in `WIPWorkOrders_Assembly`
   (Status 2 = WIP). The Sentinel enum exists in the system but is not this tool's gate.

7. **Reuse existing queries and scripts.** Before writing any new named query or function,
   check `BE_FactoryGatewayEvents.md` and `FE1_FactoryControl.md`. The entire SCC adds
   exactly ONE new named query (optional). Everything else reuses what already exists.

8. **One transform per binding.** Never chain script → query → script on a single binding.
   Complex logic goes in `StationControl.SCC`, called once from an event.

9. **Tab-indented event scripts.** All script bodies in view JSON must use real tab characters
   (`\t`) for indentation so they paste correctly into the Designer without losing a leading tab.

10. **Do not invent named queries.** Every query path used in views or scripts must exist in
    `BE_FactoryGatewayEvents.md` or `FE1_FactoryControl.md`. If you use a path, cite which
    file and line it appears on. If a genuine gap exists, flag it explicitly — don't silently
    add it.

---

## Architecture

### Gateways

| Gateway | Owns | Tag provider |
|---------|------|-------------|
| BE1 | Frame Fab, Boom Fab, Paint, Run Schedule generation | TAGIO1 |
| BE2 | Main Line, Subs, Legacy Line, Navithor fleet | TAGIO2 |

Front-ends (FE1, FE2) run the FactoryControl Perspective project. They call BE named queries
directly with `project="FactoryGatewayEvents"` (established pattern, FE1 line 12129+).
Gateway functions are fired via `system.util.sendRequest("FactoryGatewayEvents",
"executeFunction", payload={...}, remoteServer=str(GatewayConfig.getBackEnd_1/2()))`.

### Station prefix → gateway mapping

```
TW → Frame Fab  → TAGIO1 (BE1)
TT → Boom Fab   → TAGIO1 (BE1)
PT → Paint      → TAGIO1 (BE1)
TF → Main Line  → TAGIO2 (BE2)
TB → Boom Sub   → TAGIO2 (BE2)
TC → Cab Sub    → TAGIO2 (BE2)
TE → Engine Sub → TAGIO2 (BE2)
TX → Outrigger  → TAGIO2 (BE2)
LL → Legacy     → TAGIO2 (BE2)
```

Use `StationControl.DynamicView.getTagFolder(stationName)` — the EXISTING canonical resolver
in the project. Do not re-implement prefix mapping.

### Tag paths

- Station componentID: `<getTagFolder(stn)>/<stn>/control/fromIGN/componentID`
- Station AMR binding: `<getTagFolder(stn)>/<stn>/AMRControl/AMRNumberAssignedToStation`
- AMR componentID: `[TAGIO2]JLG/Jefferson City/Fleet/AMR Data/AMR_{id:03d}/machineInfo/componentID`

### WIP / Schedule status values (WIPWorkOrders_Assembly, Fabrication_*WIP)

| Value | Meaning |
|-------|---------|
| 0 | Scrapped |
| 1 | Scheduled |
| 2 | WIP (actively building) |
| 3 | Complete |
| 4 | Abort |
| 5 | Non-Conformance |
| 7 | Associated |

---

## Project file locations

All authoritative source files live in the project knowledge base (uploaded to this Claude
project). Key files:

| File | Contents |
|------|----------|
| `BE_FactoryGatewayEvents.md` | All BE named queries and script library functions |
| `FE1_FactoryControl.md` | All FE named queries and script library functions |
| `JLG_Jefferson_City_Master_System_Reference.docx` | Full system architecture |
| `CHANGELOG_PT030A_PaintUnload_GetNextWorkOrder_Refresh.md` | getNextWorkOrder refresh pattern |
| `Factory_Automation_PLC_Reference.md` | PLC tag structure (read-only reference, SCC does not gate on PLC) |
| `WorkstationAssignment.csv`, `MachineConfig.csv`, etc. | Live DB table samples |

---

## View structure

```
Station Control/station-control-center/
  scc-page/                         ← tab shell: header + button strip + single swapped ia.display.view
  tabs/
    station-componentid-rectify/    ← FEATURE 1 (first built)
    amr-componentid-rectify/
    run-schedule-refresh/
    manual-assembly-schedule/
    work-order-reconciliation/
```

### scc-page pattern

NOT `ia.container.tab`. Uses a flex row of `ia.input.button` components that set
`view.custom.selectedTab` (int 0–4), and a single `ia.display.view` whose `props.path`
is bound to a `case()` expression. This is the standard robust pattern.

### Selection pattern (all tables)

Tables fire `onSelectionChange`. Event payload shape:
```python
event.value['data']['ColumnName']   # e.g. event.value['data']['StationName']
```
Other components react to the selection by binding to `view.custom.<selectedThing>` via
property bindings. No downstream component binds directly to `Table.props.selection`.

---

## Script library: StationControl/SCC/code.py

Namespace: `StationControl.SCC`
Scope: AG (Application + Gateway)

### Public functions

| Function | What it does |
|----------|-------------|
| `stationComponentIDTagPath(stn)` | Resolves fromIGN/componentID tag path |
| `getGatewayForStation(stn)` | Returns "BE1" or "BE2" for display |
| `readStationComponentID(stn)` | One-shot tag read, no polling |
| `stationActiveWipCount(stn)` | Active WIP rows for station (boundary check) |
| `stationAmrBound(stn)` | True if AMR is bound |
| `runBoundaryChecks(stn, newID)` | Returns `{checks:[...], allPassed:bool}` |
| `commitStationComponentID(stn, newID, reason, session)` | Write + boundary + audit |
| `getAmrList()` | Tag browse of Fleet/AMR Data — no query, no polling |
| `amrComponentIDTagPath(amrId)` | AMR machineInfo/componentID path |
| `readAmrComponentID(amrId)` | One-shot AMR ID read |
| `commitAmrComponentID(amrId, newID, reason, session)` | Write + audit |
| `refreshNextWorkOrder(stn, reason, session)` | Fires getOrder + updateRunSchedules on owning BE |
| `validateSerialForAssembly(serial)` | MachineConfig check + assembly check |
| `scheduleSerialForAssembly(serial, legacy, reason, session)` | createAssemblyOrder on BE2 |
| `lookupComponent(idText)` | MachineConfig + serial/NWG resolution |
| `scheduleNwgPrePaint(componentID, itemName, reason, session)` | Prepaint routing |
| `scheduleNwgPreAssembly(componentID, reason, session)` | TF000X insert |
| `markNwgComplete(componentID, itemNumber, station, reason, session, warnIfWip)` | Mark complete |

All commit functions call `_logOverride(...)` which uses the EXISTING
`Supervisor Overrides/insert/insertEntrySupervisorOverrideLog` query.

---

## Named query reuse map (EVERY query used — verified against project files)

| SCC action | Project | Query path |
|------------|---------|-----------|
| Station list | FactoryControl | `Work Station Assignment/getWorkStationAssignmentTable` |
| MachineConfig lookup | FactoryControl | `station-control/Run Schedule/select/getMachineConfigInfo` |
| Active WIP boundary check | FactoryControl | `Station Control Center/StationComponentID/select/getActiveAssemblyStatusForStation` ← THE ONE NEW QUERY |
| Already-scheduled check | FactoryGatewayEvents | `RunSchedule/Assembly/Select/CheckScheduledStatusBySerial` |
| Scheduled serials grid | FactoryControl | `Run Schedule/Assembly/manualAssemblyScheduling/select/getAllScheduledSerialsInAssembly` |
| Serial → NWGs | FactoryGatewayEvents | `RunSchedule/Select/FindNwgsAssociatedWithSerialNumber` |
| NWG → serial | FactoryGatewayEvents | `RunSchedule/Select/FindWGSerialNumber` |
| Fab WIP status | FactoryGatewayEvents | `RunSchedule/Fabrication/Select/selectStatus` |
| Mark NWG complete | FactoryGatewayEvents | `RunSchedule/Fabrication/Select/updateCompleteTimestamp` |
| Pre-paint (boom) | FactoryControl | `Run Schedule/NonConformance/update/updateReturnBoomToPrePaint` |
| Pre-paint (frame) | FactoryControl | `Run Schedule/NonConformance/update/updateReturnFrameToPrePaint` |
| Pre-assembly TF000X | FactoryGatewayEvents | `RunSchedule/PaintUnload/insert/insertFabricationToPreAssemblyInventory` |
| Audit log | FactoryControl | `Supervisor Overrides/insert/insertEntrySupervisorOverrideLog` |

### Gateway function calls (via executeFunction + sendRequest)

| Function | Target BE |
|----------|----------|
| `RunSchedule.Assembly.Assembly.createAssemblyOrder` | BE2 |
| `RunSchedule.getNextWorkOrder.getOrder` | BE1 or BE2 (by station prefix) |
| `RunSchedule.getNextWorkOrder.updateRunSchedules` | BE1 or BE2 (by station prefix) |

---

## The ONE new named query

**Path:** `Station Control Center/StationComponentID/select/getActiveAssemblyStatusForStation`
**Project:** FactoryControl  **Type:** Scalar  **DB:** SCADA
**Param:** `stationName` (String)

```sql
SELECT COUNT(*)
FROM dbo.WIPWorkOrders_Assembly
WHERE StationName = :stationName
  AND Status = 2
  AND CompletedTimestamp IS NULL
```

Why it's new: every existing assembly WIP query requires an exact serial number parameter.
None can answer "is this station actively building regardless of serial." This is 4 lines,
read-only. Fail-safe: if not installed, `stationActiveWipCount` returns 0 and the AMR-bound
check still guards the high-risk case.

---

## Bugs found and fixed during this build (never repeat these)

| Bug | Symptom | Fix |
|-----|---------|-----|
| `onRowClick` used on tables | Nothing populated when clicking rows — silently never fired | Replaced with `onSelectionChange` everywhere |
| Theme tokens (`--textPrimary` etc.) | Text invisible / blank labels | Concrete hex colors only |
| `session.props.theme` dark mode toggle | Errors, invisible elements | Removed entirely |
| `StationControlCenter` namespace | Script calls failed — package doesn't exist | Moved to `StationControl/SCC/code.py` |
| `getStationList` invented query | "View not found" equivalent — query didn't exist | Replaced with real `Work Station Assignment/getWorkStationAssignmentTable` |
| `ia.container.tab` with parallel children | Tab content area collapsed / blank | Replaced with button strip + single `ia.display.view` swapped by `case()` expression |
| `project=_PROJECT` on BE-owned queries | Wrong project target, query not found | Corrected to `project="FactoryGatewayEvents"` for BE queries |
| `GetWipStatus_BySerialNumberAndLine` wildcarded | Query requires exact serial, % pattern unsupported | Created the one new query instead |
| Wrong `onSelectionChange` payload shape | `event.value['StationName']` throws KeyError | Real shape is `event.value['data']['StationName']` |

---

## Simulator (sim.py)

A strict Python simulator lives at `/sim/sim.py`. It:
- Mocks tags, named queries, sendRequest, session, view bindings, transforms
- Enforces real Perspective event names (lint pass catches fake events at load time)
- Tests selection → population → commit → tag write → audit log end to end

**Run before shipping any view change:** `python3 sim.py` — must show 0 failures.

To add a test: extend the test section at the bottom following the existing pattern.

---

## SupervisorOverrideLog schema (real, confirmed from live DB screenshot)

Table: `dbo.SupervisorOverrideLog`

| Column | Type | Notes |
|--------|------|-------|
| OverrideID | int identity | PK, auto |
| StationName | nvarchar | Station or ComponentID the action applied to |
| OverrideType | nvarchar | e.g. "Station ComponentID Set", "AMR ComponentID Unassign" |
| OverrideDetails | nvarchar | "before -> after" format |
| Reason | nvarchar | Required, user-entered |
| OverrideUser | nvarchar | `session.props.auth.user.userName` |
| OverrideTime | datetime | `CURRENT_TIMESTAMP` set by query |

Insert query path: `Supervisor Overrides/insert/insertEntrySupervisorOverrideLog`

---

## Access control

Gate the scc-page at the application level on roles:
```python
# Check pattern from existing FactoryControl views:
"Scheduler" in {session.props.auth.user.roles}
# Also: "Engineering", "Supervisor"
```

---

## Install checklist

1. `StationControl/SCC/code.py` — paste into new module at `StationControl → SCC` in Script Library
2. Six views imported to their paths under `Station Control/station-control-center/`
3. (Optional) one new named query added at `Station Control Center/StationComponentID/select/getActiveAssemblyStatusForStation`
4. Session message handler `sccToast` wired to your toast surface
5. scc-page gated on Engineering / Supervisor / Scheduler roles
