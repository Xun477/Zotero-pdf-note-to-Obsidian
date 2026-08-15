# -*- coding: utf-8 -*-
"""Export the AI-rewritten reading note to the Obsidian paper vault.

Reads the _note.md and its images/ directory from the MinerU output folder,
writes the note (with YAML frontmatter) plus copies the images into:

    <vault-dir>/<subdir>/<pdf_name>/<pdf_name>.md      (+ images/)

Image references stay as relative "images/xxx.png" paths, which resolve
naturally inside Obsidian because images/ lives next to the note.

Usage:
  python export_to_obsidian.py --md-file "<out>\<pdf名>_note.md" \
      --output-dir "<out>" --pdf-name "<pdf名>" --item-key <key> \
      [--vault-dir "G:\硕士\论文"] [--subdir 文献] [--compress]

Args:
  --md-file      Path to the _note.md produced by the AI rewrite step
  --output-dir   MinerU output directory (contains images/)
  --pdf-name     Paper name used for the vault folder and note filename
  --item-key     Zotero parent item key (used for the zotero frontmatter link)
  --vault-dir    Obsidian vault root (env: OBSIDIAN_VAULT_DIR, default G:\硕士\论文)
  --subdir       Subfolder inside the vault for paper notes (default 文献)
  --compress     Resize images wider than 800px, keep original format
  --user-id      Zotero user ID (default from load_creds / env ZOTERO_USER_ID)
"""

import os, re, sys, shutil, argparse, datetime

# Ensure we can import load_creds from the same directory
_script_dir = os.path.dirname(os.path.abspath(__file__))
_refs_dir = os.path.join(_script_dir, 'load_creds.py')
if not os.path.exists(_refs_dir):
    _refs_dir = os.path.expandvars(r'${USERPROFILE}\.claude\skills\Zotero pdf note to Obsidian\scripts')
    sys.path.insert(0, _refs_dir)
else:
    sys.path.insert(0, _script_dir)
from load_creds import get_user_id, load_config

# ============================================================
# Config: env var > resources/config/*.json > built-in fallback
# ============================================================
_cfg = load_config()

def _d(env_name, cfg_path, fallback):
    v = os.environ.get(env_name) if env_name else None
    if v:
        return v
    cur = _cfg
    for k in (cfg_path.split('.') if cfg_path else []):
        if not isinstance(cur, dict):
            return fallback
        cur = cur.get(k)
    return cur if cur is not None else fallback

# ============================================================
# Parse args
# ============================================================
parser = argparse.ArgumentParser(description='Export note + images to Obsidian vault')
parser.add_argument('--md-file', required=True, help='Path to the _note.md')
parser.add_argument('--output-dir', required=True, help='MinerU output dir (contains images/)')
parser.add_argument('--pdf-name', required=True, help='Paper name for vault folder/note')
parser.add_argument('--item-key', default=None, help='Zotero parent item key (for zotero link)')
parser.add_argument('--vault-dir', default=_d('OBSIDIAN_VAULT_DIR', 'paths.vault_dir', r'G:\硕士\论文'), help='Obsidian vault root (env: OBSIDIAN_VAULT_DIR)')
parser.add_argument('--subdir', default=_d(None, 'behavior.subdir', '文献'), help='Subfolder inside the vault')
parser.add_argument('--compress', action='store_true', default=None, help='Resize images >800px (default from config behavior.compress)')
parser.add_argument('--user-id', default=None, help='Zotero user ID')
args = parser.parse_args()

# --compress is a store_true flag: default=None means "not passed" -> fall back to config.
if args.compress is None:
    args.compress = bool(_cfg.get('behavior', {}).get('compress', False))

USER_ID = args.user_id or get_user_id()

# ============================================================
# Helpers
# ============================================================
IMG_REF_RE = re.compile(r'!\[[^\]]*\]\(images/([^\)]+)\)')

def sanitize(name):
    """Replace characters that Windows/Obsidian cannot use in file/folder names."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', name).strip(' .')

def yaml_str(value):
    """Collapse whitespace + quote for YAML; returns '' when empty."""
    value = re.sub(r'\s+', ' ', str(value or '').strip())
    if not value:
        return ''
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

def build_frontmatter(note, pdf_name):
    """Parse metadata from the note header and build a YAML frontmatter block."""
    fm = []
    # title: first top-level heading
    m = re.search(r'^#\s+(.+)$', note, re.MULTILINE)
    title = m.group(1).strip() if m else pdf_name
    fm.append(('title', title))
    # authors
    m = re.search(r'\*\*作者[:：]\*\*\s*(.+)', note)
    if m:
        fm.append(('authors', m.group(1).strip()))
    # journal / year
    m = re.search(r'\*\*期刊/年份[:：]\*\*\s*(.+)', note)
    if m:
        line = m.group(1).strip()
        ym = re.search(r'\b(?:19|20)\d{2}\b', line)
        year = ym.group(0) if ym else ''
        journal = re.sub(r'\b(?:19|20)\d{2}\b', '', line).rstrip(',， ') if year else line
        if year:
            fm.append(('year', year))
        if journal:
            fm.append(('journal', journal))
    # doi
    m = re.search(r'\*\*DOI[:：]\*\*\s*(\S+)', note)
    if m:
        fm.append(('doi', m.group(1).strip()))
    # fixed fields
    if args.item_key:
        fm.append(('zotero', f'https://www.zotero.org/users/{USER_ID}/items/{args.item_key}'))
    fm.append(('tags', '[文献, 论文笔记]'))
    fm.append(('created', datetime.date.today().isoformat()))

    lines = ['---']
    for key, val in fm:
        q = yaml_str(val)
        if q:
            lines.append(f'{key}: {q}')
    lines.append('---')
    return '\n'.join(lines) + '\n'

FOOTER_MARKERS = ('> 📝 本文由 MinerU 提取', '> 📁 图片目录')

def split_tail(note):
    """把结尾 footer（blockquote 及其前导 ---）从笔记中切出，返回 (body, tail)。

    捕获从第一个 footer 标记行开始、直到末尾的整段 blockquote（连续的 > 行，
    可能含 `> 📝 ...` + `> 📁 ...` 等多行）。无 footer 时返回 (note, '')。
    """
    lines = note.rstrip('\n').split('\n')
    tail_start = None
    for i, ln in enumerate(lines):
        if any(ln.strip().startswith(m) for m in FOOTER_MARKERS):
            tail_start = i
            break
    if tail_start is None:
        return note, ''
    # 向前扩展：吞掉紧跟其上的连续 > 行与空行
    while tail_start > 0 and (lines[tail_start - 1].strip().startswith('>') or not lines[tail_start - 1].strip()):
        tail_start -= 1
    # 再吞掉 footer 前的 --- 分隔线
    if tail_start > 0 and lines[tail_start - 1].strip() == '---':
        tail_start -= 1
    return '\n'.join(lines[:tail_start]), '\n'.join(lines[tail_start:])

APPENDIX_HEADING = '## 📷 全部图片 / 图片附录'

def ensure_appendix(body, tail, dst_images):
    """把磁盘上未被正文引用的图片追加到附录。幂等：以已引用文件名集合去重。"""
    existing = set(IMG_REF_RE.findall(body))
    appended = []
    if os.path.isdir(dst_images):
        for f in sorted(os.listdir(dst_images)):
            if os.path.isfile(os.path.join(dst_images, f)) and f not in existing:
                appended.append(f)
    if not appended:
        return body, tail, []
    lines = ['', APPENDIX_HEADING, '',
             f'> 以下 {len(appended)} 张图片未在正文中被引用，由导出脚本自动补齐：', '']
    lines += [f'![{f}](images/{f})' for f in appended]
    new_body = body.rstrip('\n') + '\n\n' + '\n'.join(lines) + '\n'
    return new_body, tail, appended

# ============================================================
# Read note
# ============================================================
md_file = args.md_file
if not os.path.exists(md_file):
    print(f'ERROR: note file not found: {md_file}', file=sys.stderr)
    sys.exit(1)
with open(md_file, 'r', encoding='utf-8') as f:
    note = f.read()

# ============================================================
# Build vault paths
# ============================================================
pdf_name = sanitize(args.pdf_name) or 'note'
vault_note_dir = os.path.join(args.vault_dir, args.subdir, pdf_name)
vault_note_path = os.path.join(vault_note_dir, pdf_name + '.md')
os.makedirs(vault_note_dir, exist_ok=True)

# ============================================================
# Copy images
# ============================================================
src_images = os.path.join(args.output_dir, 'images')
dst_images = os.path.join(vault_note_dir, 'images')
copied = 0
if os.path.isdir(src_images):
    os.makedirs(dst_images, exist_ok=True)
    for fname in os.listdir(src_images):
        src = os.path.join(src_images, fname)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dst_images, fname)
        if args.compress:
            try:
                from PIL import Image
                img = Image.open(src)
                w, h = img.size
                if max(w, h) > 800:
                    ratio = 800.0 / max(w, h)
                    img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                fmt = (img.format or 'JPEG').upper()
                if fmt == 'PNG':
                    img.save(dst, format='PNG', optimize=True)
                elif fmt == 'JPEG':
                    img.save(dst, format='JPEG', quality=85, optimize=True)
                else:
                    img.save(dst, format=fmt, quality=85)
            except Exception as e:
                print(f'  compress error for {fname}: {e}, copying original')
                shutil.copy2(src, dst)
        else:
            shutil.copy2(src, dst)
        copied += 1
print(f'Images copied: {copied}')

# ============================================================
# Append unreferenced images (hard guarantee: nothing dropped)
# ============================================================
body, tail = split_tail(note)
body, tail, appended = ensure_appendix(body, tail, dst_images)
note_final = (body.rstrip('\n') + '\n\n' + tail + '\n') if tail else body.rstrip('\n') + '\n'
if appended:
    print(f'[appendix] 自动补齐 {len(appended)} 张未引用图片 → {APPENDIX_HEADING}: {appended}')
else:
    print('[appendix] 所有图片均已在正文中被引用，无需补齐')

# ============================================================
# Write note with frontmatter (frontmatter parsed from ORIGINAL note)
# ============================================================
frontmatter = build_frontmatter(note, pdf_name)
with open(vault_note_path, 'w', encoding='utf-8') as f:
    f.write(frontmatter + '\n' + note_final)
print(f'Vault note: {vault_note_path}')

# ============================================================
# Verify
# ============================================================
problems = []
if not os.path.isfile(vault_note_path) or os.path.getsize(vault_note_path) == 0:
    problems.append('note file missing or empty')

headings = re.findall(r'^#{1,4}\s+', note, re.MULTILINE)
if len(headings) < 3:
    problems.append(f'note has fewer than 3 headings ({len(headings)})')

refs = IMG_REF_RE.findall(note_final)
missing = [r for r in refs if not os.path.isfile(os.path.join(dst_images, r))]
if missing:
    problems.append(f'{len(missing)} referenced image(s) missing: {missing[:3]}')
if refs and copied == 0:
    problems.append('note references images but none were copied')

# Reverse invariant: every on-disk image must now be referenced (body or appendix).
if os.path.isdir(dst_images):
    disk = set(f for f in os.listdir(dst_images) if os.path.isfile(os.path.join(dst_images, f)))
    unref = sorted(f for f in disk if f not in set(refs))
    if unref:
        problems.append(f'{len(unref)} image(s) on disk never referenced: {unref[:3]}')
else:
    disk = set()

print(f'Images on disk: {len(disk)} | '
      f'Images referenced in note: {len(set(refs))}')

if problems:
    for p in problems:
        print(f'CHECK: {p}')
    print('Result: CHECK NEEDED')
    sys.exit(1)

print('Result: OK')
