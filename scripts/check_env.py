# -*- coding: utf-8 -*-
"""环境与依赖检查（Zotero pdf note to Obsidian skill）。

逐项检查 Python 包、Zotero 凭据与 MinerU Token，输出逐项结果：
  1. httpx / Pillow 是否安装
  2. ZOTERO_API_KEY（环境变量 -> ~/.zotero_credentials -> 注册表）
  3. ZOTERO_USER_ID（环境变量或默认值，需确认是自己的 ID）
  4. MINERU_TOKEN（环境变量 -> ~/.zotero_credentials）
  5. 凭据备份文件 ~/.zotero_credentials 是否存在

有 FAIL 项时退出码 1，全部通过为 0。
用法：python check_env.py
"""

import importlib.util
import os
import sys

# Windows 控制台/管道默认用本地代码页（如 cp936/GBK），中文输出可能报
# UnicodeEncodeError 或乱码；强制 stdout/stderr 走 UTF-8，不可编码字符以替代符输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError, OSError):
        pass


def _has_pkg(name):
    return importlib.util.find_spec(name) is not None


def _cred_file():
    return os.path.expandvars(r'${USERPROFILE}\.zotero_credentials')


def _file_values():
    """读取 ~/.zotero_credentials，返回 {KEY: value}（兼容 ZOTERO_API_KEY= 与 API_KEY= 两种写法）。"""
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
    """读 HKCU\\Environment 下的用户环境变量（Zotero 凭据常存这里）。"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return str(val)
    except Exception:
        return ''


def resolve(name, aliases=()):
    """按 环境变量 -> 凭据文件（含别名）-> 注册表 顺序解析。"""
    val = os.environ.get(name, '')
    if not val:
        vals = _file_values()
        val = vals.get(name, '')
        for alias in aliases:
            if not val:
                val = vals.get(alias, '')
    if not val and name.startswith('ZOTERO_'):
        val = _registry_value(name)
    return val


def main():
    results = []   # (label, status, hint)；status: 'ok' / 'warn' / 'fail'
    has_fail = False

    # 1. Python 包
    # 注意：Pillow 安装后的 import 名是 PIL，find_spec 需查 PIL
    for pkg, display in (('httpx', 'httpx'), ('PIL', 'Pillow')):
        if _has_pkg(pkg):
            results.append((f'{display} 已安装', 'ok', ''))
        elif display == 'Pillow':
            results.append(('Pillow 未安装（可选，用于 --compress 图片压缩）', 'warn', 'pip install Pillow'))
        else:
            results.append((f'{display} 未安装', 'fail', 'pip install httpx'))
            has_fail = True

    # 2. ZOTERO_API_KEY
    api_key = resolve('ZOTERO_API_KEY', ('API_KEY',))
    results.append(('ZOTERO_API_KEY', 'ok' if api_key else 'fail',
                    '' if api_key else 'setx ZOTERO_API_KEY "你的24位密钥"，或写入 ~/.zotero_credentials（ZOTERO_API_KEY=...）'))

    # 3. ZOTERO_USER_ID
    uid = resolve('ZOTERO_USER_ID')
    if not uid:
        results.append(('ZOTERO_USER_ID', 'fail',
                        '未设置：请到 Zotero 设置 → Keys 页面获取 "Your userID for use in API calls" 后配置，或写入 ~/.zotero_credentials（ZOTERO_USER_ID=...）'))
        has_fail = True
    else:
        results.append(('ZOTERO_USER_ID', 'ok', ''))

    # 4. MINERU_TOKEN
    token = resolve('MINERU_TOKEN')
    results.append(('MINERU_TOKEN', 'ok' if token else 'fail',
                    '' if token else 'setx MINERU_TOKEN "你的Token"，或写入 ~/.zotero_credentials（MINERU_TOKEN=...）'))

    # 5. 凭据备份文件（informational，非必须：env/registry 也可）
    results.append(('凭据备份文件 ~/.zotero_credentials',
                    'ok' if os.path.exists(_cred_file()) else 'warn',
                    '可选：写入 ZOTERO_API_KEY=... 格式，仅本机使用'))

    if not (api_key and token):
        has_fail = True

    tags = {'ok': 'OK', 'warn': 'WARN', 'fail': 'FAIL'}
    for label, status, hint in results:
        print(f"[{tags[status]}]  {label}{('  ' + hint) if hint else ''}")

    print('')
    if has_fail:
        print('存在缺失项：请按上方 [FAIL] 提示补齐后重试。')
        return 1
    if any(status == 'warn' for _, status, _ in results):
        print('检查基本通过，但有可选项未满足（[WARN]），不影响主流程。')
        return 0
    print('检查通过：环境就绪。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
