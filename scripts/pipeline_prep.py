# -*- coding: utf-8 -*-
r"""Orchestrator for steps 2-5 of the Zotero PDF to Note pipeline.

Searches Zotero, locates the PDF, creates an output directory, and runs
MinerU extraction — all in one call. Outputs JSON for the agent to consume.

Usage:
  python pipeline_prep.py --query "paper title"
  python pipeline_prep.py --query "paper title" --ocr

No staging/中转 folder: MinerU output is written directly into the Obsidian
vault at <vault>/<subdir>/<pdf_name>/. Paths are configurable via env vars (or
CLI flags / resources/config/*.json, env wins):
  ZOTERO_STORAGE_DIR    Zotero attachment storage dir (default C:\path\to\Zotero\storage)
  OBSIDIAN_VAULT_DIR    Obsidian vault root (default C:\path\to\Obsidian\vault)

Output JSON:
  {"item_key": "ABC123", "title": "...", "pdf_path": "C:\\...",
   "output_dir": "C:\\path\\to\\Obsidian\\vault\\文献\\paper", "md_file": "C:\\...\\paper\\paper.md",
   "pdf_name": "paper"}

"""

import os, sys, json, argparse, subprocess, shutil

# Ensure we can import load_creds from the same directory (its module-level
# reconfigure_utf8() also fixes stdout/stderr encoding for this script).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_creds import get_api_key, get_user_id, get_mineru_token, load_config, get_config_value
from redact import redact_secrets

# ============================================================
# Config: env var > resources/config/*.json > built-in fallback
# ============================================================
_cfg = load_config()

# ============================================================
# Parse args
# ============================================================
parser = argparse.ArgumentParser(description='Zotero search + PDF locate + MinerU extract')
parser.add_argument('--query', required=True, help='Paper title or keywords')
parser.add_argument('--item-key', default=None, help='Skip search, use this Zotero item key directly')
parser.add_argument('--ocr', action='store_true', default=False, help='Enable OCR mode for MinerU')
parser.add_argument('--user-id', default=None, help='Zotero user ID')
parser.add_argument('--storage-dir', default=get_config_value(_cfg, 'ZOTERO_STORAGE_DIR', 'paths.storage_dir', r'C:\path\to\Zotero\storage'), help='Zotero attachment storage dir (env: ZOTERO_STORAGE_DIR)')
parser.add_argument('--vault-dir', default=get_config_value(_cfg, 'OBSIDIAN_VAULT_DIR', 'paths.vault_dir', r'C:\path\to\Obsidian\vault'), help='Obsidian vault root (env: OBSIDIAN_VAULT_DIR)')
parser.add_argument('--subdir', default=get_config_value(_cfg, None, 'behavior.subdir', '文献'), help='Subfolder inside the vault')
parser.add_argument('--model', default=get_config_value(_cfg, None, 'behavior.model', 'auto'), help='MinerU model: auto / vlm / pipeline / html (default: auto)')
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
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        # 不打印 URL / 原始响应正文：异常 str 含完整 URL（可能带 query），
        # 响应正文不可控，统一脱敏后只给状态码与截断字段。
        detail = redact_secrets(e.response.text[:300], (API_KEY,))
        print(f'ERROR: Zotero API 返回 {e.response.status_code}: {detail}', file=sys.stderr)
        print('检查 ZOTERO_API_KEY 是否有效：python scripts/check_env.py', file=sys.stderr)
        sys.exit(1)
    except httpx.TransportError as e:
        print(f'ERROR: 无法连接 Zotero API（{type(e).__name__}，URL 已脱敏）', file=sys.stderr)
        print('检查网络连接，或确认 api.zotero.org 可达后重试。', file=sys.stderr)
        sys.exit(1)
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
        print('修复：确认搜索词无误、该文献确实在 Zotero 库中；或改用 --item-key 直接指定条目 Key。', file=sys.stderr)
        sys.exit(1)
    # Skip saved snapshots / attachment items — they have no PDF child.
    results = [r for r in results if r.get('data', {}).get('itemType') != 'attachment']
    if not results:
        print('ERROR: Only attachment items found in Zotero.', file=sys.stderr)
        print('修复：搜索结果只有附件条目；用 --item-key 指定父条目（论文）的 Key。', file=sys.stderr)
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
    print('修复：在 Zotero 客户端给该条目添加 PDF 附件后重试（或用 --item-key 指定含 PDF 的条目）。', file=sys.stderr)
    sys.exit(1)

child_key = pdf_child.get('key', '')
child_filename = pdf_child.get('data', {}).get('filename', f'{item_key}.pdf')
pdf_path = os.path.join(args.storage_dir, child_key, child_filename)

if not os.path.exists(pdf_path):
    print(f'WARNING: PDF not found at expected path: {pdf_path}', file=sys.stderr)
    print(f'[pipeline] Will try extraction anyway (MinerU might fail)', file=sys.stderr)

print(f'[pipeline] PDF: {pdf_path}', file=sys.stderr)

# ============================================================
# Phase 3: Create output directory (directly in the Obsidian vault)
# ============================================================
pdf_name = os.path.splitext(child_filename)[0]
output_dir = os.path.join(args.vault_dir, args.subdir, pdf_name)
os.makedirs(output_dir, exist_ok=True)

# Fixed folder per paper (no _01/_02 sequence). Re-running overwrites the
# previous run: clear last run's artifacts so stale images/md never leak
# into the appendix. Keep the folder itself.
for entry in os.listdir(output_dir):
    full = os.path.join(output_dir, entry)
    if entry == 'images' and os.path.isdir(full):
        shutil.rmtree(full)
    elif os.path.isfile(full) and (entry.endswith('.md') or entry.endswith('_note.md')):
        os.remove(full)
print(f'[pipeline] Output dir: {output_dir}', file=sys.stderr)

# ============================================================
# Phase 4: MinerU extraction
# ============================================================
mineru_token = get_mineru_token()

env = os.environ.copy()
if mineru_token:
    env['MINERU_TOKEN'] = mineru_token

cmd = ['mineru-open-api', 'extract', pdf_path, '-o', output_dir, '-f', 'md']
if args.ocr:
    cmd.append('--ocr')
if args.model and args.model != 'auto':
    cmd += ['--model', args.model]

# Resolve full path: npm global packages may have .cmd wrappers not on subprocess PATH
_exe = shutil.which('mineru-open-api') or shutil.which('mineru-open-api.cmd')
if _exe:
    cmd[0] = _exe

print(f'[pipeline] Running MinerU (ocr={args.ocr}, model={args.model})...', file=sys.stderr)
timeout = get_config_value(_cfg, None, 'behavior.timeout', 120)
result = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout, shell=False)

if result.returncode != 0:
    print(f'ERROR: MinerU failed (exit {result.returncode})', file=sys.stderr)
    print(redact_secrets(result.stderr[:500], (mineru_token,)), file=sys.stderr)
    print('修复：检查 MINERU_TOKEN 是否有效（python scripts/check_env.py），或重试一次（MinerU 偶发超时）。', file=sys.stderr)
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
