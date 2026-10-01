# -*- coding: utf-8 -*-
import json, re, html, os, datetime

ROOT = r"D:\USTC-AI"
OUT = os.path.join(ROOT, "physics-faculty-directory")
os.makedirs(OUT, exist_ok=True)

SCHOOLS = [
    ("ustc",  "中国科学技术大学", "University of Science and Technology of China"),
    ("pku",   "北京大学",         "Peking University"),
    ("thu",   "清华大学",         "Tsinghua University"),
    ("nju",   "南京大学",         "Nanjing University"),
    ("sjtu",  "上海交通大学",     "Shanghai Jiao Tong University"),
    ("fudan", "复旦大学",         "Fudan University"),
    ("ucas",  "中国科学院大学",   "University of Chinese Academy of Sciences"),
]
SCHOOL_NAME = {k: cn for k, cn, en in SCHOOLS}
SCHOOL_EN = {k: en for k, cn, en in SCHOOLS}

SOURCES = os.path.join(OUT, "sources")
JOBS = [("thu", os.path.join(SOURCES, "thu.json")),
        ("pku", os.path.join(SOURCES, "pku.json")),
        ("nju", os.path.join(SOURCES, "nju.json")),
        ("sjtu", os.path.join(SOURCES, "sjtu.json")),
        ("fudan", os.path.join(SOURCES, "fudan.json")),
        ("ucas", os.path.join(SOURCES, "ucas.json"))]


def clean(v):
    if v is None:
        return ""
    return str(v).strip()


def split_title(title):
    """Split a Chinese title string into a primary role."""
    return clean(title)


def normalize(p, school):
    rec = {
        "name": clean(p.get("name") or p.get("name_local")),
        "name_local": clean(p.get("name_local")),
        "school": SCHOOL_NAME[school],
        "school_en": SCHOOL_EN[school],
        "school_key": school,
        "department": clean(p.get("department")),
        "subject": clean(p.get("subject")),
        "title": clean(p.get("title")),
        "email": clean(p.get("email")),
        "homepage": clean(p.get("homepage")),
        "profile_url": clean(p.get("profile_url")),
        "scholar_url": clean(p.get("scholar_url")),
        "lab_website": clean(p.get("lab_website")),
        "research_directions": [clean(x) for x in (p.get("research_directions") or []) if clean(x)],
        "focus_areas": [clean(x) for x in (p.get("focus_areas") or []) if clean(x)],
        "summary": clean(p.get("summary")),
        "confidence": clean(p.get("confidence")),
        "verified": bool(p.get("verified")),
        "is_academician": bool(p.get("is_academician")),
    }
    pubs = []
    for pub in (p.get("publications") or []):
        if isinstance(pub, dict):
            t = clean(pub.get("title"))
            if t:
                pubs.append({
                    "title": t,
                    "venue": clean(pub.get("venue")),
                    "year": pub.get("year") if pub.get("year") is not None else None,
                })
        elif isinstance(pub, str) and clean(pub):
            pubs.append({"title": clean(pub), "venue": "", "year": None})
    rec["publications"] = pubs[:6]
    # homepage fallback: first source URL (e.g. department list page)
    if not rec["homepage"] and not rec["profile_url"]:
        for s in (p.get("sources") or []):
            if clean(s):
                rec["homepage"] = rec["profile_url"] = clean(s)
                break
    # summary fallback
    if not rec["summary"] or rec["summary"] == "暂无内容":
        rec["summary"] = "暂无简介"
    if not rec["name_local"] and re.search(r"[\u4e00-\u9fff]", rec["name"]):
        rec["name_local"] = rec["name"]
    return rec


# ---------- USTC lab page parser ----------
def parse_ustc():
    path = os.path.join(ROOT, "ustc-physics-labs", "index.html")
    raw = open(path, "r", encoding="utf-8").read()

    def strip_tags(s):
        s = re.sub(r"<[^>]+>", "", s)
        s = html.unescape(s).strip()
        s = re.sub(r"[·\s]*\S*\.ustc\.edu\.cn\S*", "", s)  # drop trailing site url
        s = re.sub(r"^[一二三四五六七八九十]+、", "", s).strip()
        return s.strip("· ")

    records = []
    # iterate over sections -> groups -> rows, tracking current lab and section
    token_re = re.compile(
        r'<section class="school" id="[^"]*">.*?<h2>(.*?)</h2>'          # section head
        r'|<h3>(.*?)</h3>'                                                # group head
        r'|<tr class="lab"><td[^>]*>(.*?)</td></tr>'                      # lab row
        r'|<tr><th>(.*?)</th><td>(.*?)</td></tr>',                        # person row
        re.S,
    )
    section = ""
    group = ""
    lab = ""
    for m in token_re.finditer(raw):
        sec_h, grp_h, lab_h, name_h, desc_h = m.groups()
        if sec_h is not None:
            section = strip_tags(sec_h)
            group = lab = ""
        elif grp_h is not None:
            group = strip_tags(grp_h)
            lab = ""
        elif lab_h is not None:
            lab = strip_tags(lab_h)
        elif name_h is not None:
            name = strip_tags(name_h)
            desc = strip_tags(desc_h)
            hm = re.search(r'href="([^"]+)"', name_h)
            url = html.unescape(hm.group(1)) if hm else ""
            if not name:
                continue
            dept = section
            if group:
                dept = f"{section} · {group}" if section else group
            summary = desc
            if lab and lab not in desc:
                summary = f"[{lab}] {desc}"
            records.append({
                "name": name,
                "name_local": name,
                "school": SCHOOL_NAME["ustc"],
                "school_en": SCHOOL_EN["ustc"],
                "school_key": "ustc",
                "department": dept,
                "subject": "物理学 / Physics",
                "title": "",
                "email": "",
                "homepage": url,
                "profile_url": url,
                "scholar_url": "",
                "lab_website": "",
                "research_directions": [],
                "focus_areas": [],
                "summary": summary,
                "confidence": "fine" if url else "coarse",
                "verified": bool(url),
                "is_academician": ("院士" in desc),
                "publications": [],
                "lab": lab,
            })
    return records


def main():
    all_records = []
    counts = {}

    for school, path in JOBS:
        data = json.load(open(path, "r", encoding="utf-8"))
        profs = data.get("professors", [])
        recs = [normalize(p, school) for p in profs]
        counts[school] = len(recs)
        all_records.extend(recs)

    ustc = parse_ustc()
    counts["ustc"] = len(ustc)
    all_records.extend(ustc)

    # de-dup within each school by (name, department, profile_url)
    seen = set()
    deduped = []
    for r in all_records:
        key = (r["school_key"], r["name"], r.get("department", ""), r.get("profile_url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    all_records = deduped

    payload = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "schools": [{"key": k, "name": cn, "en": en, "count": counts.get(k, 0)}
                    for k, cn, en in SCHOOLS],
        "professors": all_records,
    }

    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    with open(os.path.join(OUT, "data", "faculty.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    build_html(payload)
    print("counts:", counts, "total:", len(all_records))


def build_html(payload):
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    template = open(os.path.join(OUT, "template.html"), "r", encoding="utf-8").read()
    html_out = template.replace("/*__DATA__*/", data_json)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_out)


if __name__ == "__main__":
    main()
