# -*- coding: utf-8 -*-
# Ingest an Ignition export (Designer resource export OR SCC_views_import.zip) back into
# the working view sources at ignition/views/. This is the REVERSE of rebuild_zip.py.
#
# For every "*/view.json" entry in the export, the leaf folder name is mapped to its
# ignition/views/<name>.view.json.txt via FOLDER_TXT and overwritten with the exported JSON.
# Nesting depth does not matter (same as rebuild_zip.py, which keys on split('/')[-2]).
# Unmapped view folders are REPORTED and skipped, never guessed.
#
# Usage:  python tools/ingest_zip.py <path-to-export.zip>
import zipfile, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                        # repo root (tools/ -> ..)
VIEWS = os.path.join(ROOT, 'ignition', 'views')

# KEEP IN SYNC with rebuild_zip.py FOLDER_TXT.
# zip view folder (leaf) -> ignition/views/<name>.view.json.txt
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
    'scc-flow-node': 'scc-flow-node',
    'scc-node-action': 'scc-node-action',
    'scc-overview': 'scc-overview',
    'scc-flow-canvas': 'scc-flow-canvas',
    'scc-card-assoc': 'scc-card-assoc',
    'scc-help': 'scc-help',
}

# Stashed feature; never ingest (see archive/association-TB/).
DROP = {'scc-associate-popup'}


def main(zip_path):
    if not os.path.isfile(zip_path):
        raise SystemExit('export not found: ' + zip_path)
    written, skipped, dropped = [], [], []
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if not name.endswith('/view.json'):
                continue
            folder = name.split('/')[-2]
            if folder in DROP:
                dropped.append(folder)
                continue
            if folder not in FOLDER_TXT:
                skipped.append(folder)
                continue
            data = z.read(name).decode('utf-8')
            json.loads(data)  # validate it parses before we overwrite the source
            data = data.replace('\r\n', '\n').replace('\r', '\n')  # normalize to LF (repo standard)
            out = os.path.join(VIEWS, FOLDER_TXT[folder] + '.view.json.txt')
            with open(out, 'w', encoding='utf-8', newline='') as fh:  # newline='' => emit '\n' verbatim
                fh.write(data)
            written.append(FOLDER_TXT[folder])

    print('ingested %d view(s) from %s' % (len(written), os.path.basename(zip_path)))
    for w in sorted(written):
        print('  updated  %s.view.json.txt' % w)
    if dropped:
        print('  dropped (stashed): %s' % ', '.join(sorted(set(dropped))))
    if skipped:
        print('  SKIPPED (unmapped view folders, not written):')
        for s in sorted(set(skipped)):
            print('    ! %s' % s)
    if not written:
        raise SystemExit('no mapped views found in export - is this the right zip?')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python tools/ingest_zip.py <path-to-export.zip>')
    main(sys.argv[1])
