# Station Control Center (SCC) — JLG Jefferson City

Ignition Perspective tooling inside the **FactoryControl** project at JLG Industries,
Jefferson City TN. Lets authorized users (Engineering / Supervisor / Scheduler) perform
common Station Control manual interventions without opening the Designer. Every committed
action writes to the `SupervisorOverrideLog` table.

Developer: MDI (embedded JLG resource) — Cameron Metzgar.

See [`CLAUDE.md`](CLAUDE.md) for the full build context, absolute rules, architecture, and
named-query reuse map. See [`HANDOFF.md`](HANDOFF.md) for the current build state.

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

Tracked: SCC view JSON (`files/*.view.json.txt`), script library
(`StationControl_SCC_code.py.txt`), SQL, import zips, style classes, docs, test cases.

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

### Underlying scripts (run from `files/`)
- `_rebuild_zip.py` — `*.view.json.txt` → `SCC_views_import.zip` (build the import bundle).
- `_ingest_zip.py <export.zip>` — reverse: export zip → `*.view.json.txt` (LF-normalized).

## Deploying to Ignition

The `.view.json.txt` / `code.py.txt` files are the source of truth. See the install checklist
in [`CLAUDE.md`](CLAUDE.md) for pasting them into the Designer.
