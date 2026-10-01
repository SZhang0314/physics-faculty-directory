# -*- coding: utf-8 -*-
"""Per-school profile-page summary extractors."""
import re
import textutil


def _between(h, start_pat, end_pats, dotall=True):
    m = re.search(start_pat, h, re.S | re.I)
    if not m:
        return ""
    tail = h[m.end():]
    end = None
    for ep in end_pats:
        me = re.search(ep, tail, re.S | re.I)
        if me:
            end = me.start() if end is None else min(end, me.start())
    seg = tail[:end] if end is not None else tail[:4000]
    return textutil.collapse(textutil.to_text(seg))


def _trim(s, limit=600):
    s = textutil.collapse(s)
    if len(s) > limit:
        cut = s[:limit]
        for sep in ["。", "；", "，", ". ", " "]:
            idx = cut.rfind(sep)
            if idx > limit * 0.6:
                return cut[:idx + 1]
        return cut + "…"
    return s


_HEX = re.compile(r"\b[0-9a-f]{40,}\b")

def _dehex(s):
    s = _HEX.sub(" ", s)
    s = re.sub(r"\b[0-9a-f]{24,}\b", " ", s)
    return textutil.collapse(s)


def pku(h, name):
    """Bio paragraph appears after the nav; else fall back to the trailing
    research-direction text before '网站访问量'."""
    h2 = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    seg = _between(h2, r"即可访问本教师主页",
                   [r"教育经历", r"工作经历", r"基本信息", r"研究方向.*?查看更多", r"网站访问量"])
    seg = textutil.collapse(seg)
    seg = seg.replace("暂无内容", "")
    seg = re.sub(r"^点赞[:：]?", "", seg).strip()
    seg = re.sub(r"^" + re.escape(name) + r"\s*", "", seg).strip(" ：:")
    if seg and seg != "暂无内容" and len(seg) >= 8:
        return _trim(seg)

    # fallback: research-direction line(s) between the field block and the footer
    m = re.search(r"(?:职称|教师拼音名称|所在单位)[:：].*?版权所有@北京大学", h2, re.S)
    if not m:
        m = re.search(r"研究方向.*? Research focus.*?版权所有@北京大学", h2, re.S)
    if not m:
        m = re.search(r"研究简介.*?版权所有@北京大学", h2, re.S)
    if m:
        block = _dehex(textutil.to_text(m.group(0)))
        block = re.sub(r"版权所有.*$", "", block)
        block = textutil.collapse(block)
        # drop field-explanation segments and phone/office residue
        block = re.sub(r"[：:]", "：", block)
        parts = re.split(r"(毕业院校|职称|所在单位|办公地点|联系方式|传真|电子邮箱|教师拼音名称|"
                         r"性别|学位|学历|在职信息|开通时间|最后更新时间|访问量|所在院系|手机版|"
                         r"欢迎来到我的主页|次|其他联系方式|扫描关注|个人简介|教育经历|工作经历|"
                         r"社会兼职|团队成员|https?://\S+|网站)", block)
        parts = [textutil.collapse(p).strip(" ：:，,、") for p in parts]
        parts = [p for p in parts if re.match(r"^[\u4e00-\u9fff]", p)]
        # prefer the longest genuine Chinese run
        parts = [p for p in parts if len(p) >= 8 and not re.match(
            r"^(教授|副教授|研究员|副研究员|助理教授|讲师|特任研究员|高级工程师|工程师|"
            r"物理北楼|理科楼|信息|教授)$", p)]
        if parts:
            best = max(parts, key=len)
            return _trim(best, 220)
    return ""


def nju(h, name):
    """个人简历 -> div.nr ; fallback 研究方向."""
    seg = _between(h, r'<div class="jl">.*?<p>\s*个人简历\s*</p>.*?<div class="nr">',
                   [r'<div class="jl">', r'<div class="title">\s*<p>\s*研究方向',
                    r'友情链接', r'主要课程', r'联系方式'])
    seg = textutil.collapse(seg)
    if seg:
        return _trim(seg)
    seg = _between(h, r'研究方向', [r'代表成果', r'友情链接', r'主要课程', r'联系方式', r'</div>'])
    return _trim(seg) if seg else ""


def sjtu(h, name):
    """个人经历 / 个人简介 / 研究方向 block after the name header."""
    for label in ["个人简介", "个人经历", "简介", "研究方向", "研究领域"]:
        seg = _between(h, re.escape(label),
                       [r"代表性论文", r"论文著作", r"讲授课程", r"科研项目",
                        r"地址：上海市东川路", r"沪交ICP备", r"版权所有"])
        seg = textutil.collapse(seg)
        seg = re.sub(r"^[:：\s]+", "", seg)
        if len(seg) >= 15:
            return _trim(seg)
    return ""


def fudan(h, name):
    for label in ["个人简介", "个人简历", "简介", "研究方向", "研究领域", "教育经历"]:
        seg = _between(h, re.escape(label),
                       [r"代表性论文", r"获奖信息", r"联系我们", r"Copyright", r"友情链接"])
        seg = textutil.collapse(re.sub(r"^[:：\s]+", "", seg))
        if len(seg) >= 15:
            return _trim(seg)
    return ""


def ucas(h, name):
    """people.ucas.ac.cn: 研究领域 (div.mib-c). kits / personal sites: fallback."""
    # body section: <span id="...">研究领域</span> ... <div class="mi-box"><div class="mib-c">TEXT</div>
    m = re.search(r'研究领域</span>\s*</h3>\s*<div class="mi-box">\s*<div class="mib-c">(.*?)</div>',
                  h, re.S)
    if not m:
        m = re.search(r'研究方向</span>\s*</h3>\s*<div class="mi-box">\s*<div class="mib-c">(.*?)</div>',
                      h, re.S)
    if not m:
        m = re.search(r'class="mib-c">(.*?)</div>\s*</div>', h, re.S)
    # labeled section: <h3><span id>研究领域/研究方向</span></h3><div class="mi-box"><div class="mib-c">TEXT
    for label in ["研究领域", "研究方向"]:
        mm = re.search(label + r'</span>\s*</h3>\s*<div class="mi-box">\s*<div class="mib-c">(.*?)</div>',
                       h, re.S)
        if mm:
            seg = textutil.collapse(textutil.to_text(mm.group(1)))
            seg = re.sub(r"^[:：\s]+", "", seg)
            if len(seg) >= 15:
                return _trim(seg, 400)
    # research fields inside the 个人信息 block: 研究方向 / 招生方向 / 学科专业
    txt = textutil.to_text(h)
    for label in ["研究方向", "招生方向", "研究领域"]:
        m2 = re.search(label + r"[:：]?\s*([^\n]{4,400})", txt)
        if m2:
            seg = textutil.collapse(m2.group(1))
            seg = re.split(r"(所在单位|导师类别|招生信息|学科专业|办公电话|电子邮件|"
                           r"教育背景|工作经历|个人信息)", seg)[0]
            seg = textutil.collapse(seg).strip(" ：:，,")
            if len(seg) >= 6 and re.search(r"[\u4e00-\u9fff]{4,}", seg):
                return _trim(seg, 300)
    # kits.ucas.ac.cn: Research Focus / About
    for label in ["Research Focus", "Research Interests", "Research Area", "About"]:
        seg = _between(h, re.escape(label),
                       [r"Education", r"Position", r"Publications", r"Selected",
                        r"Contact", r"Directory", r"Published:"])
        seg = textutil.collapse(re.sub(r"^[:：\s]+", "", seg))
        if len(seg) >= 25:
            return _trim(seg, 400)
    return personal_site(h, name)


def thu(h, name):
    """tsinghua body: text between the experience/teaching block and 主要论文."""
    txt = textutil.collapse(textutil.to_text(h))
    # start after the breadcrumb
    start = txt.find("首页 >")
    if start > 0:
        txt = txt[start:]
    end = re.search(r"(主要论文|主要论著|代表性论文|代表论著|发表论文|Selected Publications|"
                    r"科研项目|在研项目|获奖信息)", txt)
    body = txt[:end.start()] if end else txt
    # body now: name dept addr 邮编 电话 传真 email 主页 个人经历 教育经历 ... 工作经历 ... 教学 ... <research text>
    # drop everything up to and including the last date-bearing experience or the teaching block
    cut = max(body.rfind("工作经历"), body.rfind("教育经历"))
    seg = body[cut:] if cut > 0 else body
    seg = re.sub(r"(工作经历|教育经历|个人经历|教学|研究方向|研究领域|个人简介|"
                 r"办公室|电话|邮箱|传真|地址|邮编|主页)[:：]?", " ", seg)
    # split into clauses and drop date-bearing ones
    chunks = re.split(r"(?<=[。；;！!？?])\s*|\s{2,}", seg)
    keep = []
    for c in chunks:
        c = textutil.collapse(c)
        if not c:
            continue
        if re.search(r"\d{4}[.\-/年]|\d{2}\.\d{2}|Postdoc|Ph\.?D|博士|硕士|学士|"
                     r"University|研究员|副研究员|讲师|教授|助理教授|博士后", c):
            # experience/degree line -> skip
            continue
        if len(c) >= 6 and re.search(r"[\u4e00-\u9fff]{6,}", c):
            keep.append(c)
    if keep:
        return _trim(keep[-1], 260)
    if len(seg) >= 10:
        return _trim(seg, 220)
    return personal_site(h, name)


def personal_site(h, name):
    """Generic fallback for personal / GitHub pages: About / Bio paragraph."""
    for label in ["About me", "About", "Biography", "Bio", "个人简介", "简介", "研究兴趣", "Research interests", "Research"]:
        seg = _between(h, re.escape(label),
                       [r"Research", r"Publications", r"Teaching", r"Members",
                        r"Opening", r"News", r"Contact"])
        seg = textutil.collapse(re.sub(r"^[:：\s]+", "", seg))
        if len(seg) >= 40:
            return _trim(seg, 400)
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{40,})', h, re.I)
    if m:
        return _trim(m.group(1), 400)
    return ""


_JUNK = [
    "Research focus", "Research group", "Personal information", "Personal profile",
    "Education experience", "Work experience", "Social affiliations", "Other contact",
    "Scan attention", "版权所有", "手机版", "开通时间", "最后更新时间", "访问量",
    "教师个人主页", "中文主页", "教师名录", "学院概况", "师资队伍", "人才培养",
    "科学研究", "English", "北京大学官网", "南京大学", "上海交通大学物理", "友情链接",
    "京ICP备", "联系电话", "邮政编码", "招生信息", "教育背景", "工作经历", "教授课程",
    "出版信息", "科研活动", "基本信息", "暂无内容",
]


_FIELD_STOP = re.compile(
    r"(办公地点|联系方式|传真|电子邮箱|教师拼音名称|邮政编码|邮编|电话|室$|楼\d|"
    r"网站|访问量|手机版|下一页|上一页|点击|更多|返回|版权所有)")


def is_valid_summary(s):
    """Reject nav/boilerplate. Require >=12 chars and a real Chinese clause."""
    if not s:
        return False
    s = textutil.collapse(s)
    if len(s) < 10:
        return False
    if _FIELD_STOP.search(s):
        return False
    if re.search(r"\d{3,}-\d{5,}", s):  # phone
        return False
    if re.match(r"^[：:，,、\s]", s):
        return False
    junk_hits = sum(1 for j in _JUNK if j in s)
    if junk_hits >= 2:
        return False
    if any(j in s for j in ("版权所有", "教师个人主页", "中文主页", "Research focus",
                            "Personal information", "友情链接", "京ICP备")):
        return False
    # need a plausible Chinese clause OR a multi-word English description
    if re.search(r"[\u4e00-\u9fff]{6,}", s):
        return True
    words = re.findall(r"[A-Za-z]{3,}", s)
    if len(words) >= 3 and len(s) >= 20 and not re.search(
            r"(Site Map|Internet Explorer|JavaScript|Directory|Postdoctoral|"
            r"About From|For Visitors|Find Us|Login|Skip to)", s):
        return True
    return False


EXTRACTORS = {
    "pku": pku, "nju": nju, "sjtu": sjtu,
    "fudan": fudan, "ucas": ucas, "thu": thu,
}
