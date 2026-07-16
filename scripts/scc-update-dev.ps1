<#
.SYNOPSIS
    Update the dev branch from an Ignition view export, tagging the old dev state first.

.DESCRIPTION
    Workflow this automates (in order):
      1. Verify you are on a clean 'dev' branch and sync with origin.
      2. Ingest the export (Designer export .zip or SCC_views_import.zip) into the
         *.view.json.txt sources, then rebuild files/SCC_views_import.zip.
      3. If (and only if) that produced real content changes:
           a. Tag the CURRENT (pre-update) dev commit as a snapshot  -> old version preserved.
           b. Commit the update on dev.
           c. Push the branch and the snapshot tag to origin.
      4. If nothing really changed, revert the working tree and exit without tagging.

.PARAMETER Export
    Path to the export file (an Ignition Designer view export .zip, or SCC_views_import.zip).

.PARAMETER Message
    Commit message for the dev update. Defaults to a stamped generic message.

.PARAMETER Tag
    Snapshot tag name for the OLD dev state. Defaults to dev-snapshot-<yyyyMMdd-HHmmss>.

.EXAMPLE
    .\scripts\scc-update-dev.ps1 -Export "$HOME\Downloads\StationControlCenter_export.zip" -Message "Add serial filter to work-order recon"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Export,
    [string]$Message,
    [string]$Tag
)

$ErrorActionPreference = 'Stop'

# Repo root = parent of this script's folder.
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# --- 0. sanity -------------------------------------------------------------
if (-not (Test-Path $Export)) { Fail "export file not found: $Export" }
$Export = (Resolve-Path $Export).Path

$branch = "$(git rev-parse --abbrev-ref HEAD)".Trim()
if ($branch -ne 'dev') { Fail "you are on '$branch', not 'dev'. Switch with: git checkout dev" }

$dirty = git status --porcelain --untracked-files=no   # $null when tree is clean
if ($dirty) {
    Fail "dev has uncommitted changes. Commit or stash them before running this."
}

# --- 1. sync dev with origin ----------------------------------------------
Write-Host "==> syncing dev with origin" -ForegroundColor Cyan
git fetch origin dev
git merge --ff-only origin/dev
if ($LASTEXITCODE -ne 0) { Fail "dev is not fast-forwardable from origin/dev. Reconcile manually." }

# --- 2. ingest -------------------------------------------------------------
Write-Host "==> ingesting export into *.view.json.txt" -ForegroundColor Cyan
python files/_ingest_zip.py "$Export"
if ($LASTEXITCODE -ne 0) { git checkout -- files/; Fail "ingest failed; working tree reverted." }

# --- 3. real SOURCE changes? -----------------------------------------------
# Gate on the *.view.json.txt sources, NOT the derived zip (the zip re-deflates on
# every rebuild and can differ byte-wise even when no view actually changed).
# 'git diff --quiet' evaluates normalized content, so EOL-only noise is ignored.
git diff --quiet -- 'files/*.view.json.txt'
if ($LASTEXITCODE -eq 0) {
    Write-Host "No view changes from that export - nothing to update. Reverting." -ForegroundColor Yellow
    git checkout -- files/
    exit 0
}

Write-Host "==> view sources changed; rebuilding SCC_views_import.zip" -ForegroundColor Cyan
python files/_rebuild_zip.py
if ($LASTEXITCODE -ne 0) { git checkout -- files/; Fail "rebuild failed; working tree reverted." }
git add -A

# --- 4. tag OLD dev, then commit the update -------------------------------
if (-not $Tag)     { $Tag     = "dev-snapshot-$(Get-Date -Format 'yyyyMMdd-HHmmss')" }
if (-not $Message) { $Message = "Update dev from export ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))" }

Write-Host "==> tagging old dev as $Tag" -ForegroundColor Cyan
git tag -a $Tag -m "dev snapshot before: $Message"   # tags current HEAD (pre-update)

Write-Host "==> committing update on dev" -ForegroundColor Cyan
git commit -q -m "$Message"

Write-Host "==> pushing dev + tag $Tag" -ForegroundColor Cyan
git push origin dev
git push origin $Tag

Write-Host ""
Write-Host "Done. Old dev preserved at tag '$Tag'; dev updated and pushed." -ForegroundColor Green
Write-Host "  restore old:  git checkout $Tag" -ForegroundColor DarkGray
