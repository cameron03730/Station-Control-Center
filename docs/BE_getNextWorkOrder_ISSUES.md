# Backend `getNextWorkOrder` — why it "keeps failing in places" (BE fix list)

**File (live):** FactoryGatewayEvents → `RunSchedule/getNextWorkOrder/code.py`
**Reference copy analyzed:** `Plant reference docs/gwbk_extract_be/.../RunSchedule/getNextWorkOrder/code.py` (1691 lines, from the 2026-06-23 BE backup).

These are **back-end** defects — they must be fixed and deployed on the BE gateway (BE1/BE2), not in the SCC. The SCC now (session 11d) treats a `getNextWorkOrder` failure as a **background, non-fatal** event: the Mark WIP / Mark Complete / ComponentID change still commits, the full BE traceback is written to the gateway log (`STATION CONTROL CENTER` logger), and the user only sees a calm "use Refresh Next Work Order if the station didn't update" note. So these no longer break the SCC — but fixing them makes the auto-refresh actually work.

**Systemic root cause:** almost no `system.tag.readBlocking(...)` result in this file checks `.quality` before using `.value`, and many dataset lookups assume a column exists / a row matched. Any uninitialized or bad-quality tag, or any schedule dataset with an unexpected shape, throws. That is exactly "fails in places" — it's station/data-state dependent.

## Top fixes (ranked by how often they're hit)

1. **`getTagFolder()` unmapped-prefix — fires on the FIRST line of every call.** `getOrder`/`updateRunSchedules` do `baseTagPath = StationControl.DynamicView.getTagFolder(stationName) + "/" + stationName + "/runSchedule"`. `StationControl.DynamicView.getTagFolder` leaves its local `tagPath` unassigned for a prefix it doesn't recognize → `UnboundLocalError` (or returns `None` → `TypeError` on the `+`). **Fix:** in `getTagFolder`, initialize `tagPath = ''` at the top and `return None` for unknown prefixes; in `getNextWorkOrder`, after the call add `if not stationFolderPath: return False`. (This is the same `getTagFolder` bug already noted in the SCC tag-structure memo.)

2. **`int(tagValue)` on a possibly-null tag — `stationType` / `stationScheduleConfig`.** Lines ~28, ~93: `int(system.tag.readBlocking(base+"/stationType")[0].value)`. If the tag is uninitialized/bad-quality, `.value` is `None` → `TypeError: int() argument must be a string or a number, not 'NoneType'`. **Fix:** read the QualifiedValue, check `.quality.isGood()` and `value is not None` before `int()`; bail cleanly otherwise.

3. **`getStationQuery` config-5 returns `None` into `appendDataset`/`writeBlocking`.** In the `stationScheduleConfig == 5` path (e.g. TT0700), when `wipItem` is non-empty but no schedule row matches, `resultDataset` stays `None`, then `system.dataset.appendDataset(resultDataset, filteredData)` throws. **Fix:** `if resultDataset is None: resultDataset = filteredData` (or return `filteredData`).

4. **Paint Unload (`stationType == 5`): `nextID` used before assignment (~line 568).** When both `carrierCompID` and `carrierCompID2` are non-empty but neither `if/elif` branch matches (both parts already scanned — a normal mid-cycle state), `nextID` is never set → `NameError`/`UnboundLocalError` at the `writeBlocking`. **Fix:** initialize `nextID = carrierCompID` (or `componentID`) before the `if`.

5. **`populateItemNumber` — `getColumnIndex('X') == -1` then `getValueAt(row, -1)`.** Runs for every stationType-3 fab station. The tag-backed `Secondary Frame/Boom Schedule` datasets can be empty/uninitialized after a gateway restart, or drift on column names (`'Item Name'` with a space vs `'ItemName'`). A missing column → `getColumnIndex` returns -1 → `ArrayIndexOutOfBoundsException`. **Fix:** validate `getRowCount() > 0` and that each needed column index `>= 0` before the list comprehensions.

## Also worth fixing (lower frequency)
- **Paint Unload unguarded MachineConfig row-0 access (~line 711):** `getMachineConfigInfo(onDeckComponentID,['ItemName']).getValueAt(0,'Value')` throws if the component has no `ItemName` row (empty dataset). The sibling at ~589 is already wrapped in try/except; mirror it here (or check `getRowCount() > 0`).
- **Paint Unload loop-match variables used before assignment (~603/604, 664, 743/749, 759/765):** when a carrier/on-deck lookup returns rows but none match the scanned id, `carrierCompKitNumber` / `carrierGroupID` / `carrierOrder` / `onDeck*` are never assigned → `NameError`. **Fix:** initialize to `None` before each loop and branch on `None`.
- **`filterDataset` (~1181):** `columnNames.index('ItemNumber')` raises `ValueError` if that column is absent; the ComponentID/SerialNumber fallback also throws if both are missing. **Fix:** guard with membership checks.
- **`parallelStationsNextComponentDecision` (~1568):** labeled "CURRENTLY NOT BEING USED" but it IS called at ~line 113 for `TW030A/TW030B/TW030C`. It has the same null-`stationRunSchedule` / `getColumnIndex('ComponentID')==-1` risks, and can fall through and return `None` (caller then returns `None` to the SCC instead of True/False). **Fix:** guard the null/column cases and return a definite bool.

## After deploying these
Re-test the SCC "Refresh Next Work Order" button and the auto-refresh after Mark WIP / Mark Complete. Until then, the SCC behaves correctly (action commits; a failed refresh is logged, not shown as an action error).
