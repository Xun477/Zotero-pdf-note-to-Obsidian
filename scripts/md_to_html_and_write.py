# -*- coding: utf-8 -*-
"""Merged: MD→HTML conversion + Zotero write + verify. Single script, single call.

Usage:
  python md_to_html_and_write.py --md-file <path> --output-dir <dir> --item-key <key> [--compress]

Args:
  --md-file      Path to the structured note MD file (_note.md)
  --output-dir   Output directory (also contains images/ subdirectory)
  --item-key     Zotero parent item key
  --compress     If set, use PIL to resize images (max 400px, JPEG quality 60)
  --user-id      Zotero user ID (default: from env ZOTERO_USER_ID)
"""
import re, os, base64, json, sys, argparse, time

# Add skill scripts/ to path so we can import load_creds
# Try the actual scripts/ dir first (works when script is run from temp)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_refs_dir = os.path.join(_script_dir, 'load_creds.py')
if not os.path.exists(_refs_dir):
    # We're running a copy from temp — point to the real scripts/
    _refs_dir = os.path.expandvars(r'${USERPROFILE}\.claude\skills\Zotero pdf note to Obsidian\scripts')
    sys.path.insert(0, _refs_dir)
else:
    sys.path.insert(0, _script_dir)
from load_creds import get_api_key, get_user_id

# ============================================================
# Parse args
# ============================================================
parser = argparse.ArgumentParser(description='MD→HTML→Zotero note writer')
parser.add_argument('--md-file', required=True, help='Path to _note.md')
parser.add_argument('--output-dir', required=True, help='Output directory (contains images/)')
parser.add_argument('--item-key', required=True, help='Zotero parent item key')
parser.add_argument('--compress', action='store_true', default=False, help='Compress images with PIL')
parser.add_argument('--user-id', default=None, help='Zotero user ID')
args = parser.parse_args()

md_file = args.md_file
output_dir = args.output_dir
images_dir = os.path.join(output_dir, 'images')
html_file = os.path.join(output_dir, os.path.splitext(os.path.basename(md_file))[0] + '.html')
ITEM_KEY = args.item_key
USER_ID = args.user_id or get_user_id()
COMPRESS = args.compress

# ============================================================
# Credential loading (delegated to load_creds.py)
# ============================================================
API_KEY = get_api_key()

# ============================================================
# Phase 1: MD → HTML conversion
# ============================================================
print(f'Reading MD: {md_file}')
with open(md_file, 'r', encoding='utf-8') as f:
    md = f.read()

# --- 1a: Markdown tables → HTML tables ---
def md_table_to_html(md_table):
    lines = [l.strip() for l in md_table.strip().split('\n') if l.strip().startswith('|')]
    if len(lines) < 2:
        return md_table
    rows = [[c.strip() for c in l.split('|')[1:-1]] for l in lines]
    header = rows[0]
    is_sep = all(re.match(r'^[-:]+$', c) for c in rows[1]) if len(rows) > 1 else False
    data = rows[2:] if is_sep else rows[1:]
    h = '<table style="border-collapse:collapse;width:100%;margin:8px 0;">\n<thead><tr>\n'
    for cell in header:
        h += f'<th style="border:1px solid #999;padding:4px 8px;background:#e0e0e0;"><strong>{cell}</strong></th>\n'
    h += '</tr></thead>\n<tbody>\n'
    for row in data:
        h += '<tr>\n'
        for cell in row:
            cell = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
            h += f'<td style="border:1px solid #ccc;padding:4px 8px;">{cell}</td>\n'
        h += '</tr>\n'
    h += '</tbody></table>'
    return h

for match in re.finditer(r'((?:^\|.+\|.*$\n?)+)', md, re.MULTILINE):
    orig = match.group(1)
    if re.search(r'\|[-:]+\|', orig):
        md = md.replace(orig, md_table_to_html(orig))

# --- 1b: Images → Base64 (with optional compression) ---
img_count = 0
if COMPRESS:
    try:
        from PIL import Image
        import io
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
        print('WARNING: PIL not installed, falling back to original-size images')
else:
    HAS_PIL = False

for m in re.finditer(r'!\[([^\]]*)\]\(images/([^\)]+)\)', md):
    alt, fname = m.group(1), m.group(2)
    fpath = os.path.join(images_dir, fname)
    if not os.path.exists(fpath):
        continue
    if HAS_PIL:
        try:
            img = Image.open(fpath)
            w, h = img.size
            if w > 400:
                ratio = 400.0 / w
                img = img.resize((400, int(h * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=60, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        except Exception as e:
            print(f'  PIL error for {fname}: {e}, using original')
            with open(fpath, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
    else:
        with open(fpath, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
    img_count += 1
    tag = f'<p><strong>{alt}</strong></p><p><img src="data:image/jpeg;base64,{b64}" style="max-width:500px;width:100%;border:1px solid #ccc;border-radius:4px;"></p>'
    md = md.replace(m.group(0), tag)
print(f'Images embedded: {img_count}')

# --- 1c: Remaining MD → HTML ---
tbl_blocks = {}
for i, m in enumerate(re.finditer(r'<table.*?</table>', md, re.DOTALL)):
    key = f'__TBL_{i}__'; tbl_blocks[key] = m.group(0); md = md.replace(m.group(0), key)

md = re.sub(r'^#### (.+)$', r'<h5>\1</h5>', md, flags=re.MULTILINE)
md = re.sub(r'^### (.+)$', r'<h4>\1</h4>', md, flags=re.MULTILINE)
md = re.sub(r'^## (.+)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)
md = re.sub(r'^# (.+)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
md = re.sub(r'(?<![<\w])\*([^*\n]+)\*(?![>\w])', r'<em>\1</em>', md)
md = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', md, flags=re.MULTILINE)
md = re.sub(r'`([^`]+)`', r'<code>\1</code>', md)
md = md.replace('\n---\n', '\n<hr>\n')

for key, block in tbl_blocks.items():
    md = md.replace(key, block)

paragraphs = md.split('\n\n')
parts = []
for p in paragraphs:
    p = p.strip()
    if not p: continue
    if p.startswith('<h') or p.startswith('<table') or p.startswith('<blockquote') or p.startswith('<hr') or p.startswith('<p>'):
        parts.append(p)
    else:
        if '\n' in p: p = p.replace('\n', '<br>\n')
        parts.append(f'<p>{p}</p>')

note_html = '\n'.join(parts)
note_html = re.sub(r'<p>\s*</p>', '', note_html)

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(note_html)
print(f'HTML written: {html_file} ({len(note_html)} chars)')

# ============================================================
# Phase 2: POST to Zotero Web API
# ============================================================
import httpx

url = f'https://api.zotero.org/users/{USER_ID}/items/'
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

payload = [{
    'parentItem': ITEM_KEY,
    'itemType': 'note',
    'note': note_html
}]

json_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')

# Retry loop: 3 attempts with exponential backoff for transient network errors
note_key = None
for attempt in range(3):
    try:
        resp = httpx.post(url, headers=headers, content=json_bytes, timeout=60)
        break
    except (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
        if attempt < 2:
            wait = 2 ** attempt  # 1s, 2s
            print(f'Network error (attempt {attempt+1}/3): {e}')
            print(f'Retrying in {wait}s...')
            time.sleep(wait)
        else:
            raise

print(f'Write Status: {resp.status_code}')
if resp.status_code in [200, 201]:
    result = resp.json()
    # Handle both response formats: {"successful":{"0":{"key":"..."}}} and {"success":{"0":"..."}}
    if 'successful' in result and result['successful']:
        note_key = list(result['successful'].values())[0].get('key')
    elif 'success' in result and result['success']:
        val = list(result['success'].values())[0]
        note_key = val if isinstance(val, str) else val.get('key')
    print(f'Note Key: {note_key}')
else:
    print(f'Error: {resp.text[:500]}')
    sys.exit(1)

if not note_key:
    print('ERROR: Could not extract note key from response.')
    print(f'Full response: {resp.text[:1000]}')
    sys.exit(1)

# ============================================================
# Phase 3: Verify
# ============================================================
verify = httpx.get(
    f'https://api.zotero.org/users/{USER_ID}/items/{note_key}',
    headers={'Authorization': f'Bearer {API_KEY}'},
    timeout=30
)
if verify.status_code == 200:
    stored_note = verify.json()['data']['note']
    # Paper template (7-section IMRaD) checks
    paper_en = ['Author', 'Key words', 'Abstract', 'Introduction',
                'Experimental method', 'Result and Discussion', 'Conclusion']
    paper_en_ok = sum(1 for c in paper_en if c in stored_note) >= 7
    # General template checks
    general_en = ['Overview', '个人评注']
    general_ok = sum(1 for c in general_en if c in stored_note) >= 2
    # Legacy CN fallback
    cn_checks = ['作者背景', '关键词', '个人评注']
    cn_ok = sum(1 for c in cn_checks if c in stored_note) >= 3
    passed = paper_en_ok or general_ok or cn_ok
    print(f'Verify — Paper IMRaD: {sum(1 for c in paper_en if c in stored_note)}/{len(paper_en)} | General: {sum(1 for c in general_en if c in stored_note)}/{len(general_en)} | CN fallback: {sum(1 for c in cn_checks if c in stored_note)}/{len(cn_checks)}')
    print(f'Result: {"OK" if passed else "CHECK NEEDED"}')
else:
    print(f'Verify Error: {verify.status_code} - {verify.text[:200]}')
