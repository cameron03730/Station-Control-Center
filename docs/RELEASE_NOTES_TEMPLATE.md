# SCC vX.Y.Z — <short release title>

**Release date:** YYYY-MM-DD
**Environment promoted to:** dev → test → prod (note which gateway this build is live on)
**Ignition project:** FactoryControl · JLG Jefferson City
**Git tag:** `vX.Y.Z`  ·  **Import bundle:** `SCC_views_import.zip` (attach below)

---

## Summary
_One short paragraph: what this release delivers and why it matters to the operators/
schedulers who use it._

## What's new
- **<Feature / tab name>** — what it does, who uses it.

## Changed
- **<view or script>** — what changed and the user-visible effect.

## Fixed
- **<bug>** — symptom → cause → fix. Reference the CLAUDE.md "bugs found" table if relevant.

## Deployment steps (Designer)
1. Import `SCC_views_import.zip` to
   `Plant Overview/Engineering/Station Control Center/`.
2. Paste `StationControl_SCC_code.py.txt` into `StationControl → SCC` in the Script Library.
3. Deploy/verify named queries: `getActiveStations`,
   `getFabricationScheduleByComponent`, `getAssemblyScheduleBySerial`.
4. Confirm scc-page is gated on Engineering / Supervisor / Scheduler.
5. Smoke-test one commit per tab; confirm a row lands in `SupervisorOverrideLog`.

## Rollback
- Re-import the previous release's `SCC_views_import.zip` (attached to the prior release),
  or `git checkout v<prev>` and re-package.
- The pre-update dev snapshot tag `dev-snapshot-<stamp>` also captures the prior state.

## Verification
- [ ] `python sim.py` → 0 failures
- [ ] Each tab: selection → populate → commit → tag write → audit row confirmed
- [ ] No polling bindings introduced (`polling.enabled = false` everywhere)

## Named-query / script dependencies
_List any query path or `StationControl.SCC` function added or changed, so the DBA/next dev
knows what must exist in the target gateway._

## Known issues / follow-ups
- _..._
