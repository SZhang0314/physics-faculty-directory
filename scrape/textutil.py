# -*- coding: utf-8 -*-
import re, html as H

_SCRIPT = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def to_text(h):
    h = _SCRIPT.sub(" ", h)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|tr|h[1-6]|section)>", "\n", h, flags=re.I)
    h = _TAG.sub(" ", h)
    h = H.unescape(h)
    h = h.replace("\u200b", "").replace("\xa0", " ").replace("\ufeff", "")
    h = re.sub(r"[ \t]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h


def collapse(s):
    return re.sub(r"\s+", " ", s or "").strip()


def first_email(s):
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s or "")
    return m.group(0) if m else ""


NAV_WORDS = [
    "版权所有", "Copyright", "ICP备", "京公网安备", "网站地图", "联系我们",
    "首页", "登录", "English", "中文",
]
