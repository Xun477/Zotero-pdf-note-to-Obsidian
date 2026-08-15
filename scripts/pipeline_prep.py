# -*- coding: utf-8 -*-
"""Orchestrator for steps 2-5 of the Zotero PDF to Note pipeline.

Searches Zotero, locates the PDF, creates an output directory, and runs
MinerU extraction — all in one call. Outputs JSON for the agent to consume.

Usage:
  python pipeline_prep.py --query "paper title" --base-dir "G:\硕士\ai\中转"
  python pipeline_prep.py --query "paper title" --base-dir "..." --ocr

Paths are configurable via env vars (or --base-dir / --storage-dir):
  ZOTERO_NOTE_BASE_DIR   base output dir for notes (default G:\硕士\ai\中转)
  ZOTERO_STORAGE_DIR     Zotero attachment storage dir (default G:\硕士\Zotero\storage)

Output JSON:
  {"item_key": "ABC123", "title": "...", "pdf_path": "G:\\...",
   "output_dir": "G:\\...\\paper_01", "md_file": "G:\\...\\paper_01\\paper.md",
   "pdf_name": "paper"}

"""

import os, sys, json, argparse, subprocess, re

# Ensure we can import load_creds from the same directory
_script_dir = os.path.dirname(os.path.abspath(__file__))
_refs_dir = os.path.join(_script_dir, 'load_creds.py')
if not os.path.exists(_refs_dir):
    _refs_dir = os.path.expandvars(r'${USERPROFILE}\.claude\skills\Zotero pdf note to Obsidian\scripts')
    sys.path.insert(0, _refs_dir)
else:
    sys.path.insert(0, _script_dir)
from load_creds import get_api_key, get_user_id

# ============================================================
# Parse args
# ============================================================
parser = argparse.ArgumentParser(description='Zotero search + PDF locate + MinerU extract')
parser.add_argument('--query', required=True, help='Paper title or keywords')
parser.add_argument('--item-key', default=None, help='Skip search, use this Zotero item key directly')
parser.add_argument('--base-dir', default=os.environ.get('ZOTERO_NOTE_BASE_DIR', r'G:\硕士\ai\中转'), help='Base output directory (env: ZOTERO_NOTE_BASE_DIR)')
parser.add_argument('--ocr', action='store_true', default=False, help='Enable OCR mode for MinerU')
parser.add_argument('--user-id', default=None, help='Zotero user ID')
parser.add_argument('--storage-dir', default=os.environ.get('ZOTERO_STORAGE_DIR', r'G:\硕士\Zotero\storage'), help='Zotero attachment storage dir (env: ZOTERO_STORAGE_DIR)')
args = parser.parse_args()

API_KEY = get_api_key()
USER_ID = args.user_id or get_user_id()

# ============================================================
# Helper: Zotero Web API request
# ============================================================
import httpx

def zotero_get(path, **params):
    url = f'https://api.zotero.org/users/{USER_ID}/{path}'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    resp = httpx.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

# ============================================================
# Phase 1: Search or use provided item key
# ============================================================
if args.item_key:
    item_key = args.item_key
    # Fetch item metadata for title
    try:
        item_data = zotero_get(f'items/{item_key}')
        item_title = item_data.get('data', {}).get('title', 'Unknown')
    except Exception:
        item_title = 'Unknown'
    print(f'[pipeline] Using provided item key: {item_key} ({item_title})', file=sys.stderr)
else:
    print(f'[pipeline] Searching Zotero for: {args.query}', file=sys.stderr)
    results = zotero_get('items', q=args.query, limit=5)
    if not results:
        print('ERROR: No items found in Zotero.', file=sys.stderr)
        sys.exit(1)
    # Skip saved snapshots / attachment items — they have no PDF child.
    results = [r for r in results if r.get('data', {}).get('itemType') != 'attachment']
    if not results:
        print('ERROR: Only attachment items found in Zotero.', file=sys.stderr)
        sys.exit(1)
    # Pick the first result
    first = results[0]
    item_key = first.get('key', '')
    item_title = first.get('data', {}).get('title', 'Unknown')
    print(f'[pipeline] Found: [{item_key}] {item_title}', file=sys.stderr)
    if len(results) > 1:
        titles = [r.get('data', {}).get('title', '?') for r in results]
        print(f'[pipeline] Multiple results ({len(results)}): {titles}', file=sys.stderr)
        print(f'[pipeline] Using first match. Override with --item-key if wrong.', file=sys.stderr)

# ============================================================
# Phase 2: Find PDF attachment
# ============================================================
print(f'[pipeline] Getting children for {item_key}...', file=sys.stderr)
children = zotero_get(f'items/{item_key}/children')
pdf_child = None
for child in children:
    content_type = child.get('data', {}).get('contentType', '')
    if content_type == 'application/pdf':
        pdf_child = child
        break

if not pdf_child:
    print('ERROR: No PDF attachment found.', file=sys.stderr)
    sys.exit(1)

child_key = pdf_child.get('key', '')
child_filename = pdf_child.get('data', {}).get('filename', f'{item_key}.pdf')
pdf_path = os.path.join(args.storage_dir, child_key, child_filename)

if not os.path.exists(pdf_path):
    print(f'WARNING: PDF not found at expected path: {pdf_path}', file=sys.stderr)
    print(f'[pipeline] Will try extraction anyway (MinerU might fail)', file=sys.stderr)

print(f'[pipeline] PDF: {pdf_path}', file=sys.stderr)

# ============================================================
# Phase 3: Create output directory
# ============================================================
pdf_name = os.path.splitext(child_filename)[0]
base_dir = args.base_dir

# Find existing dirs with same prefix, increment sequence
existing = []
if os.path.isdir(base_dir):
    for name in os.listdir(base_dir):
        full = os.path.join(base_dir, name)
        if os.path.isdir(full) and name.startswith(pdf_name):
            m = re.search(r'_(\d+)$', name)
            if m:
                existing.append(int(m.group(1)))

seq = max(existing) + 1 if existing else 1
folder_name = f'{pdf_name}_{seq:02d}'
output_dir = os.path.join(base_dir, folder_name)
os.makedirs(output_dir, exist_ok=True)
print(f'[pipeline] Output dir: {output_dir}', file=sys.stderr)

# ============================================================
# Phase 4: MinerU extraction
# ============================================================
mineru_token = os.environ.get('MINERU_TOKEN', '')
if not mineru_token:
    # Try to load from user env var
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
        mineru_token, _ = winreg.QueryValueEx(k, 'MINERU_TOKEN')
        winreg.CloseKey(k)
    except Exception:
        pass

env = os.environ.copy()
if mineru_token:
    env['MINERU_TOKEN'] = mineru_token

cmd = ['mineru-open-api', 'extract', pdf_path, '-o', output_dir, '-f', 'md']
if args.ocr:
    cmd.append('--ocr')

# Resolve full path: npm global packages may have .cmd wrappers not on subprocess PATH
import shutil
_exe = shutil.which('mineru-open-api') or shutil.which('mineru-open-api.cmd')
if _exe:
    cmd[0] = _exe

print(f'[pipeline] Running MinerU (ocr={args.ocr})...', file=sys.stderr)
result = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120, shell=False)

if result.returncode != 0:
    print(f'ERROR: MinerU failed (exit {result.returncode})', file=sys.stderr)
    print(result.stderr[:500], file=sys.stderr)
    sys.exit(1)

md_file = os.path.join(output_dir, f'{pdf_name}.md')
if not os.path.exists(md_file):
    # Try alternate filename
    candidates = [f for f in os.listdir(output_dir) if f.endswith('.md')]
    if candidates:
        md_file = os.path.join(output_dir, candidates[0])
    else:
        print(f'WARNING: No .md file found in {output_dir}', file=sys.stderr)

print(f'[pipeline] MD file: {md_file}', file=sys.stderr)

# ============================================================
# Phase 5: Output JSON for agent
# ============================================================
output = {
    'item_key': item_key,
    'title': item_title,
    'pdf_path': pdf_path,
    'output_dir': output_dir,
    'md_file': md_file,
    'pdf_name': pdf_name
}
print(json.dumps(output, ensure_ascii=False))
