# -*- coding: utf-8 -*-
r"""Credential loading for Zotero API. Three-tier fallback:
  1. Environment variable ZOTERO_API_KEY
  2. Credentials file ~/.zotero_credentials
  3. Windows Registry (HKCU\Environment\ZOTERO_API_KEY)

Also loads the non-secret JSON config (paths + behavior) from:
  resources/config/config.json   (user override)
  resources/config/config.example.json  (shipped defaults, fallback)

Usage:
  from load_creds import get_api_key, get_user_id, get_mineru_token, load_config, get_config_value
  api_key = get_api_key()  # exits with code 1 if not found
"""

import os
import sys
import json


def reconfigure_utf8():
    """Windows 控制台/管道默认用本地代码页（如 cp936/GBK），中文输出可能报
    UnicodeEncodeError 或乱码；强制 stdout/stderr 走 UTF-8，不可编码字符以替代符输出。"""
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


reconfigure_utf8()


def _cred_file():
    return os.path.expandvars(r'${USERPROFILE}\.zotero_credentials')


def _file_values():
    """读取 ~/.zotero_credentials，返回 {KEY: value}（兼容 ZOTERO_API_KEY= / API_KEY= 等写法）。"""
    vals = {}
    path = _cred_file()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        k, _, v = line.partition('=')
                        vals[k.strip()] = v.strip()
        except OSError:
            pass
    return vals


def _registry_value(name):
    r"""读 HKCU\Environment 下的用户环境变量（Zotero 凭据常存这里）。"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return str(val)
    except Exception:
        return ''


def _resolve(name, aliases=(), registry=False):
    """按 环境变量 -> 凭据文件（含别名）-> 注册表 顺序解析（与 check_env.py 行为对齐）。"""
    val = os.environ.get(name, '')
    if not val:
        vals = _file_values()
        val = vals.get(name, '')
        for alias in aliases:
            if not val:
                val = vals.get(alias, '')
    if not val and (registry or name.startswith('ZOTERO_')):
        val = _registry_value(name)
    return val


def get_api_key():
    """Return ZOTERO_API_KEY from first available source. Exit if not found."""
    api_key = _resolve('ZOTERO_API_KEY', ('API_KEY',))
    if not api_key:
        print('ERROR: Cannot load ZOTERO_API_KEY from env, file, or registry.')
        print('修复：setx ZOTERO_API_KEY "你的24位密钥"，或写入 ~\\.zotero_credentials（ZOTERO_API_KEY=...），然后重开终端。')
        sys.exit(1)
    return api_key


def get_user_id():
    """Return ZOTERO_USER_ID from env, file, or registry (no built-in default)."""
    return _resolve('ZOTERO_USER_ID')


def get_mineru_token():
    """Return MINERU_TOKEN from env, file, or registry."""
    return _resolve('MINERU_TOKEN', registry=True)


def load_config():
    """Load non-secret JSON config from resources/config.

    Priority: config.json (user override) -> config.example.json (shipped
    defaults) -> {} (built-in fallback). Returns {} on missing/corrupt file
    or non-dict root, so callers always get a dict and never crash.
    """
    cfg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'resources', 'config')
    for name in ('config.json', 'config.example.json'):
        path = os.path.join(cfg_dir, name)
        try:
            # utf-8-sig tolerates a UTF-8 BOM (Windows editors may add one).
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


def get_config_value(cfg, env_name, cfg_path, fallback):
    """环境变量 > 嵌套 dict 配置路径 > fallback（原各脚本 _d() 逻辑，统一于此）。"""
    v = os.environ.get(env_name) if env_name else None
    if v:
        return v
    cur = cfg
    for k in (cfg_path.split('.') if cfg_path else []):
        if not isinstance(cur, dict):
            return fallback
        cur = cur.get(k)
    return cur if cur is not None else fallback
