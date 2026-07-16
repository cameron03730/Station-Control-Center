# Changelog

All notable changes to the Station Control Center (SCC) are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.

- **MAJOR** — breaking change to a view contract, script signature, or named-query dependency.
- **MINOR** — new tab/feature or capability, backward compatible.
- **PATCH** — bug fix or copy/style change, no behavior contract change.

## [Unreleased]
### Added
### Changed
### Fixed

---

## [1.0.0] — 2026-07-16
First production release of the Station Control Center inside the FactoryControl project.

### Added
- **scc-page** tab shell — button-strip navigation over a single swapped `ia.display.view`
  (no `ia.container.tab`), gated on Engineering / Supervisor / Scheduler roles.
- **Station ComponentID Rectify** — read/verify/commit a station's `fromIGN/componentID`
  with WIP + AMR-bound boundary checks before write.
- **AMR ComponentID Rectify** — read/commit an AMR's `machineInfo/componentID`.
- **Run Schedule Refresh** — fires `getOrder` + `updateRunSchedules` on the owning backend.
- **Manual Assembly Schedule** — serial validation + `createAssemblyOrder` on BE2.
- **Work Order Reconciliation** — component/serial schedule lookup and mark-complete (WG + NWG).
- **StationControl.SCC** script library (`StationControl/SCC/code.py`) — all read/commit logic;
  every commit writes to `SupervisorOverrideLog` via the existing insert query.
- Three read-only FactoryControl named queries: `getActiveStations`,
  `getFabricationScheduleByComponent`, `getAssemblyScheduleBySerial`.
- Ignition import bundle `files/SCC_views_import.zip` (19 views) and rebuild tool
  `files/_rebuild_zip.py`.

### Notes
- No polling bindings anywhere; all data refreshes on demand.
- Concrete hex colors only (no theme tokens); no dark mode.

[Unreleased]: https://github.com/cameron03730/Station-Control-Center/compare/v1.0.0...dev
[1.0.0]: https://github.com/cameron03730/Station-Control-Center/releases/tag/v1.0.0
