# -*- coding: utf-8 -*-
"""Credential loading for Zotero API. Three-tier fallback:
  1. Environment variable ZOTERO_API_KEY
  2. Credentials file ~/.zotero_credentials
  3. Windows Registry (HKCU\Environment\ZOTERO_API_KEY)

Usage:
  from load_creds import get_api_key
  api_key = get_api_key()  # exits with code 1 if not found
"""

import os
import sys


def get_api_key():
    """Return ZOTERO_API_KEY from first available source. Exit if not found."""
    api_key = os.environ.get('ZOTERO_API_KEY', '')

    if not api_key:
        cred_file = os.path.expandvars(r'${USERPROFILE}\.zotero_credentials')
        if os.path.exists(cred_file):
            with open(cred_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
            api_key, _ = winreg.QueryValueEx(key, 'ZOTERO_API_KEY')
            winreg.CloseKey(key)
        except Exception:
            pass

    if not api_key:
        print('ERROR: Cannot load ZOTERO_API_KEY from env, file, or registry.')
        sys.exit(1)

    return api_key


def get_user_id(default='21068406'):
    """Return ZOTERO_USER_ID from env, or fall back to default."""
    return os.environ.get('ZOTERO_USER_ID', default)
