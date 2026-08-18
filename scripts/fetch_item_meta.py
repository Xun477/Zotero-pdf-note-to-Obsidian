# -*- coding: utf-8 -*-
"""Fetch full Zotero item metadata for a given item key (print as JSON)."""
import os, sys, json, argparse, httpx

# Windows 控制台/管道默认用本地代码页（如 cp936/GBK），中文输出可能报
# UnicodeEncodeError 或乱码；强制 stdout/stderr 走 UTF-8，不可编码字符以替代符输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError, OSError):
        pass

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)
from load_creds import get_api_key, get_user_id
from redact import redact_secrets

parser = argparse.ArgumentParser()
parser.add_argument('--item-key', required=True)
args = parser.parse_args()

API_KEY = get_api_key()
USER_ID = get_user_id()

url = f'https://api.zotero.org/users/{USER_ID}/items/{args.item_key}'
headers = {'Authorization': f'Bearer {API_KEY}'}
resp = httpx.get(url, headers=headers, timeout=30)
try:
    resp.raise_for_status()
except httpx.HTTPStatusError as e:
    # 异常 str 含完整 URL，不打印；响应正文脱敏后只给状态码与截断字段。
    detail = redact_secrets(e.response.text[:300], (API_KEY,))
    print(f'ERROR: Zotero API 返回 {e.response.status_code}: {detail}', file=sys.stderr)
    print('检查 ZOTERO_API_KEY 是否有效：python scripts/check_env.py', file=sys.stderr)
    sys.exit(1)
except httpx.TransportError as e:
    print(f'ERROR: 无法连接 Zotero API（{type(e).__name__}，URL 已脱敏）', file=sys.stderr)
    print('检查网络连接，或确认 api.zotero.org 可达后重试。', file=sys.stderr)
    sys.exit(1)
data = resp.json().get('data', {})

out = {
    'title': data.get('title', ''),
    'publicationTitle': data.get('publicationTitle', ''),
    'DOI': data.get('DOI', ''),
    'date': data.get('date', ''),
    'itemType': data.get('itemType', ''),
    'creators': [
        {'firstName': c.get('firstName', ''), 'lastName': c.get('lastName', '')}
        for c in data.get('creators', [])
    ],
}
print(json.dumps(out, ensure_ascii=False, indent=2))
