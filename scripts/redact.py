# -*- coding: utf-8 -*-
"""错误消息凭据脱敏（借鉴 modlens 的 redact.ts）。

进错误消息的任何文本（异常 str、响应正文、URL）先过这里，确保终端、
JSON 输出与 agent 上下文里不出现密钥。原则：宁可脱敏过度——多脱敏的
错误消息仍可读、可行动，泄露的 key 不可挽回（"a leaked key does not"）。
"""

import re

# 常见 token 形状的第二层网（第一层是已知值精确替换）。Erring toward
# redacting too much: over-redacted errors stay actionable.
_TOKEN_SHAPES = [
    # Vendor-prefixed keys (OpenAI/Anthropic sk-, Stripe rk/pk, Slack xox*).
    re.compile(r'\b(?:sk|rk|pk|xox[a-z])-[A-Za-z0-9_-]{12,}\b'),
    # Google API keys.
    re.compile(r'\bAIza[A-Za-z0-9_-]{20,}\b'),
    # GitHub tokens.
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    # JWTs (three base64url segments, the first spelling {"alg" or {"typ").
    re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}\b'),
    # Auth headers: "Bearer xyz" / "Authorization: xyz".
    re.compile(r'\b(?:bearer|authorization)\b[=:\s]+"?[A-Za-z0-9._~+/-]{12,}"?', re.IGNORECASE),
    # Labeled keys need an explicit = or : separator.
    re.compile(r'\b(?:token|api[-_]?key)\b\s*[=:]\s*"?[A-Za-z0-9._~+/-]{12,}"?', re.IGNORECASE),
]

# URL-shaped token carrying possible userinfo: scheme, then anything up to a
# space containing an '@'. Loose on purpose — masking only happens when the
# credential regex confirms real userinfo after the '@'.
_URL_CANDIDATE = re.compile(r'\b[a-z][a-z0-9+.-]*:[^ ]*@[^ ]*', re.IGNORECASE)
_RAW_USERINFO = re.compile(r'^([a-z][a-z0-9+.-]*:[\\/]{2,4})[^\s/?#]*@', re.IGNORECASE)


def redact_secrets(text, known_secrets=None):
    """脱敏一段要进错误消息的文本。

    1. 已知密钥值精确替换（长度 >= 6，避免误伤普通短词）
    2. token 形状正则（第二层网）
    3. 每个 URL 形态的 token 检查 userinfo（http://u:p@host -> http://***@host）
    """
    out = str(text)
    for secret in known_secrets or ():
        if secret and len(secret) >= 6:
            out = out.replace(secret, '[redacted]')
    for shape in _TOKEN_SHAPES:
        out = shape.sub('[redacted]', out)
    out = _URL_CANDIDATE.sub(lambda m: mask_url_credentials(m.group(0)), out)
    return out


def mask_url_credentials(url):
    """把 URL 中的 userinfo 掩掉：http://alice:s3cr3t@proxy:8080 -> http://***@proxy:8080。

    只重写确实带凭据的 URL（@ 后有非空 username/password）；无凭据的 URL 原样返回。
    """
    parsed = None
    try:
        parsed = __import__('urllib.parse', fromlist=['urlsplit']).urlsplit(url)
    except Exception:
        return url
    if parsed is None:
        return url
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ''
        if parsed.port:
            netloc = f'{netloc}:{parsed.port}'
        return f'{parsed.scheme}://***@{netloc}{parsed.path}{"?" + parsed.query if parsed.query else ""}{"#" + parsed.fragment if parsed.fragment else ""}'
    return url


if __name__ == '__main__':
    # 自检：跑一段样例，确认脱敏生效（不打印任何真实凭据）。
    samples = [
        ('key sk-abcdefghijklmnop in text', 'key [redacted] in text'),
        ('Bearer eyJhbGciOiJIUzI1NiJ9.abcdefgh.UVWXYZ12 in text', 'Bearer [redacted] in text'),
        ('http://alice:s3cr3t@proxy:8080/path', 'http://***@proxy:8080/path'),
        ('no secrets here', 'no secrets here'),
    ]
    for raw, expected in samples:
        got = redact_secrets(raw, ('my-realkey-0123456789abcdef',))
        status = 'OK' if got == expected else f'FAIL (got: {got!r})'
        print(f'[{status}] {raw!r} -> {got!r}')
    # 已知值替换自检
    got = redact_secrets('leaked my-realkey-0123456789abcdef end', ('my-realkey-0123456789abcdef',))
    print(f'[{"OK" if got == "leaked [redacted] end" else "FAIL"}] known-value redaction: {got!r}')
