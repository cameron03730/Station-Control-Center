# -*- coding: utf-8 -*-
# Rebuild SCC_views_import.zip from the working *.view.json.txt sources (run from files/).
# - Replaces every existing view.json from its matching .txt (folder->txt map below).
# - Copies non-view entries (resource.json, thumbnail.png, project.json) verbatim.
# - Adds NEW_EMBEDDED views with a clean resource.json (files:['view.json'], no thumbnail/signature).
# Usage:  python _rebuild_zip.py    (cwd = files/)
import zipfile, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, 'SCC_views_import.zip')
BASE = 'com.inductiveautomation.perspective/views/Plant Overview/Engineering/Station Control Center/'

# zip folder (last path segment) -> files/<name>.view.json.txt
FOLDER_TXT = {
    'work-order-reconciliation': 'work-order-reconciliation',
    'station-componentID-rectify': 'station-componentid-rectify',  # folder has capital ID
    'amr-componentid-rectify': 'amr-componentid-rectify',
    'manual-assembly-schedule': 'manual-assembly-schedule',
    'Station-Control-Center': 'scc-page',
    'scc-card-schedule': 'scc-card-schedule',
    'scc-card-station': 'scc-card-station',
    'scc-card-amr': 'scc-card-amr',
    'scc-card-serial': 'scc-card-serial',
    'scc-toast-popup': 'scc-toast-popup',
    'scc-confirm-dialog': 'scc-confirm-dialog',
    'scc-action-progress': 'scc-action-progress',
    'scc-serial-row': 'scc-serial-row',
    # Machine Overview feature (added 2026-06-26):
    'scc-flow-node': 'scc-flow-node',
    'scc-node-action': 'scc-node-action',
    'scc-overview': 'scc-overview',
    'scc-flow-canvas': 'scc-flow-canvas',
    'scc-card-assoc': 'scc-card-assoc',
    'scc-help': 'scc-help',
}

# View folders to DROP from the zip entirely (feature stashed for later; source lives under
# files/_stash_association_TB/). scc-associate-popup = the boom-association editor, removed 2026-07-01.
DROP = {'scc-associate-popup'}

# Views that do NOT yet exist as folders in the current zip and must be appended (embedded/).
NEW_EMBEDDED = ['scc-flow-node', 'scc-node-action', 'scc-overview', 'scc-flow-canvas', 'scc-card-assoc', 'scc-help']

CLEAN_RESOURCE = json.dumps({
    "scope": "G", "version": 1, "restricted": False, "overridable": True,
    "files": ["view.json"],
    "attributes": {"lastModification": {"actor": "external", "timestamp": "2026-06-26T00:00:00Z"}},
}, indent=2)


def read_txt(name):
    with open(os.path.join(HERE, name + '.view.json.txt'), 'r', encoding='utf-8') as fh:
        s = fh.read()
    json.loads(s)  # validate it parses
    return s


old = zipfile.ZipFile(ZIP, 'r')
entries = []          # (arcname, bytes)
seen_folders = set()  # view folders already in the zip
for info in old.infolist():
    name = info.filename
    # Skip every entry (view.json + resource.json + thumbnail) under a dropped/stashed view folder.
    if any(('/' + drop + '/') in name for drop in DROP):
        continue
    if name.endswith('/view.json'):
        folder = name.split('/')[-2]
        seen_folders.add(folder)
        if folder not in FOLDER_TXT:
            raise SystemExit('UNMAPPED view folder in zip: ' + folder)
        entries.append((name, read_txt(FOLDER_TXT[folder]).encode('utf-8')))
    else:
        entries.append((name, old.read(name)))
old.close()

# Append any NEW_EMBEDDED view that wasn't already a folder in the zip.
for nm in NEW_EMBEDDED:
    if nm in seen_folders:
        continue
    folder = BASE + 'embedded/' + nm + '/'
    entries.append((folder + 'view.json', read_txt(nm).encode('utf-8')))
    entries.append((folder + 'resource.json', CLEAN_RESOURCE.encode('utf-8')))

with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for arc, data in entries:
        z.writestr(arc, data)

z = zipfile.ZipFile(ZIP, 'r')
nviews = sum(1 for n in z.namelist() if n.endswith('/view.json'))
print('rebuilt %s' % ZIP)
print('total entries: %d ; views: %d ; bytes: %d' % (len(z.namelist()), nviews, os.path.getsize(ZIP)))
z.close()
