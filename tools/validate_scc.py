# -*- coding: utf-8 -*-
# Lightweight SCC validator (stands in for sim.py lint while sim.py isn't present here).
# Checks: JSON validity, code.py Python syntax, banned theme tokens, onRowClick,
# tab-indented script bodies, and reports every event-script body found.
import json, ast, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                        # repo root (tools/ -> ..)
VIEWS_DIR = os.path.join(ROOT, 'ignition', 'views')
CODE_PATH = os.path.join(ROOT, 'ignition', 'script-library', 'StationControl_SCC_code.py.txt')
VIEWS = [f for f in os.listdir(VIEWS_DIR) if f.endswith('.view.json.txt')]
CODE = 'StationControl_SCC_code.py.txt'

THEME_TOKEN_RE = re.compile(r'(?<![A-Za-z0-9])--(?:text|container|accent|neutral|primary|secondary|surface|background|foreground)', re.I)
VARFUNC_RE = re.compile(r'var\(\s*--')

fail = 0
def err(m):
    global fail; fail += 1; print('  FAIL: ' + m)

print('=== JSON validity ===')
parsed = {}
for v in sorted(VIEWS):
    p = os.path.join(VIEWS_DIR, v)
    try:
        with open(p, 'r', encoding='utf-8') as fh:
            parsed[v] = json.load(fh)
        print('  ok   ' + v)
    except Exception as e:
        err('%s did not parse: %s' % (v, e))

print('=== code.py Python syntax ===')
cp = CODE_PATH
try:
    src = open(cp, 'r', encoding='utf-8').read()
    ast.parse(src)
    print('  ok   ' + CODE)
except Exception as e:
    err('%s syntax error: %s' % (CODE, e))

# Walk helper: yield (jsonpath, key, value) for every string
def walk(node, path=''):
    if isinstance(node, dict):
        for k, val in node.items():
            np = path + '/' + str(k)
            if isinstance(val, str):
                yield (np, k, val)
            else:
                for x in walk(val, np):
                    yield x
    elif isinstance(node, list):
        for i, val in enumerate(node):
            np = path + '[%d]' % i
            if isinstance(val, str):
                yield (np, None, val)
            else:
                for x in walk(val, np):
                    yield x

print('=== banned theme tokens (--textPrimary, var(--...), etc.) ===')
hits = 0
for v, tree in parsed.items():
    for pth, k, s in walk(tree):
        if THEME_TOKEN_RE.search(s) or VARFUNC_RE.search(s):
            hits += 1; err('%s %s -> %r' % (v, pth, s[:80]))
if hits == 0:
    print('  ok   no theme tokens in any view')

print('=== onRowClick (must be zero) ===')
hits = 0
for v, tree in parsed.items():
    for pth, k, s in walk(tree):
        if 'onRowClick' in (k or '') or 'onRowClick' in s:
            hits += 1; err('%s %s' % (v, pth))
if hits == 0:
    print('  ok   no onRowClick anywhere')

print('=== event/transform script bodies must start with a TAB ===')
# Find every "script" string that is a non-empty multi-statement body under a config
bad = 0; total = 0
def find_scripts(node, path=''):
    if isinstance(node, dict):
        for k, val in node.items():
            np = path + '/' + str(k)
            if k == 'script' and isinstance(val, str) and val.strip():
                yield (np, val)
            else:
                for x in find_scripts(val, np):
                    yield x
    elif isinstance(node, list):
        for i, val in enumerate(node):
            for x in find_scripts(val, path + '[%d]' % i):
                yield x
for v, tree in parsed.items():
    for pth, body in find_scripts(tree):
        total += 1
        first = body.split('\n', 1)[0]
        # allow leading blank lines, but the first non-empty content line must be tab-indented
        lines = [ln for ln in body.split('\n') if ln.strip() != '']
        if lines and not lines[0].startswith('\t'):
            bad += 1; err('%s %s first code line not tab-indented: %r' % (v, pth, lines[0][:60]))
print('  scanned %d script bodies; %d not tab-indented' % (total, bad))

print('=== scc-page tab labels (rename check) ===')
sp = parsed.get('scc-page.view.json.txt')
if sp:
    found = json.dumps(sp)
    labels = ['Station Rectification', 'AMR Rectification', 'Manual Assembly', 'Work Order Reconciliation']
    for lab in labels:
        if lab in found:
            print('  ok   tab label present: ' + lab)
        else:
            err('tab label missing: ' + lab)
    for old in ['Station ComponentID', 'AMR ComponentID']:
        if old in found:
            err('old tab label still present: ' + old)

print()
print('RESULT: ' + ('ALL CHECKS PASSED' if fail == 0 else ('%d FAILURE(S)' % fail)))
sys.exit(1 if fail else 0)
