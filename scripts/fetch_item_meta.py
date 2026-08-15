# -*- coding: utf-8 -*-
"""Fetch full Zotero item metadata for a given item key (print as JSON)."""
import os, sys, json, argparse, httpx

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)
from load_creds import get_api_key, get_user_id

parser = argparse.ArgumentParser()
parser.add_argument('--item-key', required=True)
args = parser.parse_args()

API_KEY = get_api_key()
USER_ID = get_user_id()

url = f'https://api.zotero.org/users/{USER_ID}/items/{args.item_key}'
headers = {'Authorization': f'Bearer {API_KEY}'}
resp = httpx.get(url, headers=headers, timeout=30)
resp.raise_for_status()
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
