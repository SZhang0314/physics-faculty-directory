# -*- coding: utf-8 -*-
"""Enrich missing summaries for one school's data/faculty.json."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch, extract, textutil

ROOT = r"D:\USTC-AI"
SRC = {k: None for k in ("pku", "thu", "nju", "sjtu", "fudan", "ucas")}
SOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources")


def is_missing(p):
    s = (p.get("summary") or "").strip()
    return (not s) or s == "暂无内容" or s.startswith("暂无")


def url_of(p):
    u = (p.get("profile_url") or p.get("homepage") or "").strip()
    # fix malformed UCAS links like people.ucas.ac.cn/http://people.ucas.ac.cn/~x
    m = re.search(r"(people\.ucas\.ac\.cn)/(~[A-Za-z0-9_]+)", u)
    if m:
        u = "https://" + m.group(1) + "/" + m.group(2)
    return u


def run(school, workers=8, limit=None):
    path = os.path.join(SOURCES_DIR, school + ".json")
    data = json.load(open(path, "r", encoding="utf-8"))
    profs = data["professors"]
    targets = [p for p in profs if is_missing(p) and url_of(p)]
    if limit:
        targets = targets[:limit]
    print(f"[{school}] missing-with-url: {len(targets)} / {len(profs)}")

    urls = [url_of(p) for p in targets]
    t0 = time.time()

    def prog(d, t):
        print(f"  fetched {d}/{t} ({time.time()-t0:.0f}s)", flush=True)

    pages = fetch.fetch_many(urls, workers=workers, use_cache=True, progress=prog)

    ex = extract.EXTRACTORS[school]
    filled = 0
    failed = []
    for p in targets:
        u = url_of(p)
        h = pages.get(u)
        if not h:
            failed.append((p.get("name"), u, "fetch-fail"))
            continue
        try:
            s = ex(h, p.get("name") or "")
        except Exception as e:
            s = ""
            failed.append((p.get("name"), u, f"exc:{e}"))
        if s and extract.is_valid_summary(s):
            p["summary"] = s
            filled += 1
        else:
            failed.append((p.get("name"), u, "no-summary"))

    # recompute confidence
    for p in profs:
        if p.get("summary") and p.get("summary") not in ("暂无内容",) and (url_of(p)):
            if p.get("confidence") == "coarse" and p.get("research_directions"):
                p["confidence"] = "fine"
    data["professors"] = profs
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"[{school}] filled {filled} / {len(targets)}  ({time.time()-t0:.0f}s)")
    log = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"failed_{school}.txt")
    with open(log, "w", encoding="utf-8") as f:
        for n, u, r in failed:
            f.write(f"{n}\t{u}\t{r}\n")
    print(f"  failures logged: {len(failed)} -> {log}")
    return filled, len(targets)


if __name__ == "__main__":
    school = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    run(school, workers=workers, limit=limit)
