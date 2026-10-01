# -*- coding: utf-8 -*-
"""Concurrent page fetcher with on-disk cache."""
import os, ssl, hashlib, urllib.request, urllib.error, time
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _cache_path(url):
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE, key + ".html")


def fetch(url, use_cache=True, timeout=25, retries=2):
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp):
        try:
            return open(cp, "r", encoding="utf-8").read()
        except Exception:
            pass
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })
            raw = urllib.request.urlopen(req, timeout=timeout, context=_CTX).read()
            text = _decode(raw)
            if _is_blocked(text):
                last = RuntimeError("blocked")
                time.sleep(3.0 * (attempt + 1))
                continue
            with open(cp, "w", encoding="utf-8") as f:
                f.write(text)
            return text
        except Exception as e:
            last = e
            time.sleep(0.6 * (attempt + 1))
    raise last


BLOCK_MARKERS = ["访问过于频繁", "系统封禁", "请稍后再试", "Access Denied", "Forbidden"]


def _is_blocked(text):
    if len(text) < 1500 and any(m in text for m in BLOCK_MARKERS):
        return True
    return False


def _decode(raw):
    # try utf-8 then gb18030
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def fetch_many(urls, workers=8, use_cache=True, progress=None):
    """Return dict url -> html (or None on failure)."""
    out = {}
    uniq = list(dict.fromkeys(u for u in urls if u))
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch, u, use_cache): u for u in uniq}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                out[u] = fut.result()
            except Exception:
                out[u] = None
            done += 1
            if progress and done % 20 == 0:
                progress(done, len(uniq))
    if progress:
        progress(len(uniq), len(uniq))
    return out
