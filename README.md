# Station Control Center (SCC) — JLG Jefferson City

Ignition Perspective tooling inside the **FactoryControl** project at JLG Industries,
Jefferson City TN. Lets authorized users (Engineering / Supervisor / Scheduler) perform
common Station Control manual interventions without opening the Designer. Every committed
action writes to the `SupervisorOverrideLog` table.

Developer: MDI (embedded JLG resource) — Cameron Metzgar.

See [`CLAUDE.md`](CLAUDE.md) for the full build context, absolute rules, architecture, and
named-query reuse map. See [`docs/HANDOFF.md`](docs/HANDOFF.md) for the current build state.

## Repository layout

```
ignition/                Deployable Ignition resources (the product)
  script-library/        StationControl.SCC  (StationControl_SCC_code.py.txt)
  views/                 Perspective view sources (*.view.json.txt)
  named-queries/         Named-query SQL (*.sql.txt)
  style-classes/         Perspective style classes (SCC_Primary, SCC_Success)
  import-bundle/         SCC_views_import.zip  (rebuilt from views/ by tools/rebuild_zip.py)
tools/                   Build + validation scripts (run from the repo root)
docs/                    Guides, release-notes template, build/handoff notes
reference/               Plant reference material (tag exports, PLC, overview)
tests/                   Test-case workbook (.xlsm)
archive/                 Parked/retired feature source (e.g. association-TB)
scripts/                 scc-update-dev.ps1 (local dev-update helper)
.github/workflows/       "Package SCC Views" action
```

## Branch model — one branch per environment

| Branch | Mirrors | Rule |
|--------|---------|------|
| `dev`  | Dev Ignition gateway  | **Active work happens here.** All changes land on `dev` first. |
| `test` | Test / staging gateway | Managed release branch. Promote from `dev` when a change is ready to validate. |
| `prod` | Production gateway     | Managed release branch. Reflects exactly what is live in production. |

Promotion flows **dev → test → prod**. `test` and `prod` are only updated by promoting a
reviewed change up from the branch below — never by committing directly.

```
# daily work
git checkout dev
# ...make changes, commit...
git push origin dev

# promote dev -> test (when ready to validate)
git checkout test && git merge dev && git push origin test

# promote test -> prod (when validated & deployed live)
git checkout prod && git merge test && git push origin prod
```

## What is / isn't tracked

Tracked: view sources (`ignition/views/*.view.json.txt`), script library
(`ignition/script-library/StationControl_SCC_code.py.txt`), named-query SQL, the import
bundle, style classes, docs, and the test-case workbook.

Ignored (see `.gitignore`): `.cache/`, `*.gwbk` gateway backups, extracted `gwbk_extract*/`
folders (derived + break Windows path limits), and machine-local `.claude/settings.local.json`.

## Tooling / workflows

### Pull the latest views as a zip (GitHub Action)
Actions tab → **Package SCC Views** → **Run workflow** → pick a branch → download the
`SCC_views_import_<branch>` artifact. It rebuilds `SCC_views_import.zip` from that branch's
`*.view.json.txt` sources. (GitHub wraps artifacts in an outer zip — unzip once to get the
bundle.) Requires the workflow to exist on the default branch to appear.

### Push edits back to dev, preserving the old version (local script)
After exporting your edited views from the Designer, run from the repo root:
```powershell
.\scripts\scc-update-dev.ps1 -Export "C:\path\to\StationControlCenter_export.zip" -Message "what changed"
```
It (1) verifies you're on a clean `dev`, (2) ingests the export into the `.txt` sources and
rebuilds the bundle, and — only if a view actually changed — (3) tags the current dev as
`dev-snapshot-<timestamp>` (so the old version is preserved), then commits and pushes `dev`.
Restore any old snapshot with `git checkout <tag>`. Pass `-Tag <name>` to name the snapshot.

### Underlying scripts (in `tools/`, run from the repo root)
- `python tools/rebuild_zip.py` — `ignition/views/*.view.json.txt` → `ignition/import-bundle/SCC_views_import.zip`.
- `python tools/ingest_zip.py <export.zip>` — reverse: export zip → `ignition/views/*.view.json.txt` (LF-normalized).
- `python tools/validate_scc.py` — lint the views + `ast.parse` the script library.
- `python tools/gen_help.py` / `python tools/gen_overview.py` — regenerate the Help / Machine-Overview views.

## Deploying to Ignition

The `.view.json.txt` / `code.py.txt` files are the source of truth. See the install checklist
in [`CLAUDE.md`](CLAUDE.md) for pasting them into the Designer.
