# -*- coding: utf-8 -*-
"""Copy canonical per-school faculty.json into sources/.
THU data is read from git HEAD of the tsinghua repo (its working tree may differ)."""
import subprocess, json, os

ROOT = r"D:\USTC-AI"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources")
os.makedirs(OUT, exist_ok=True)

SRC = {
    "pku":   r"pku-physics-directory\data\faculty.json",
    "nju":   r"nju-physics-directory\data\faculty.json",
    "sjtu":  r"sjtu-physics-directory\data\faculty.json",
    "fudan": r"fudan-physics-directory\data\faculty.json",
    "ucas":  r"ucas-physics-directory\data\faculty.json",
}
for key, rel in SRC.items():
    if key in ("pku", "nju", "sjtu", "fudan", "ucas"):
        repo = os.path.join(ROOT, rel.split("\\")[0])
        committed = os.path.join(repo, "data", "faculty.json")
        if os.path.exists(committed):
            data = json.load(open(committed, encoding="utf-8"))
        else:
            data = json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))
    json.dump(data, open(os.path.join(OUT, key + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(key, len(data.get("professors", [])))

out = subprocess.check_output(["git", "-C", os.path.join(ROOT, "prof-directory"),
                               "show", "HEAD:data/faculty.json"])
data = json.loads(out.decode("utf-8"))
json.dump(data, open(os.path.join(OUT, "thu.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("thu", len(data.get("professors", [])))
