# 中国高校物理教师汇总 / Physics Faculty Directory

把以下 7 所学校已有的物理教师汇总网页合并成的**单一可检索页面**，
并按中科大标准（**每位教师都有简介 + 主页链接**）补齐了各校缺失的简介。

| 学校 | 来源仓库 | 收录 | 简介覆盖 | 主页链接 |
|---|---|---|---|---|
| 中国科学技术大学 | `ustc-physics-labs` | 227 | 100% | 100% |
| 北京大学 | `pku-physics-directory` | 266 | 77% | 100% |
| 清华大学 | `tsinghua-physics-faculty` | 189 | 97% | 100% |
| 南京大学 | `nju-physics-directory` | 643 | 76% | 100% |
| 上海交通大学 | `sjtu-physics-directory` | 198 | 91% | 100% |
| 复旦大学 | `fudan-physics-directory` | 163 | 90% | 100% |
| 中国科学院大学 | `ucas-physics-faculty` | 314 | 82% | 100% |
| **合计** | | **2000** | **84%** | **100%** |

> 抓不到简介的老师显示「暂无简介」，但**主页链接始终保留**（含院系列表页兜底）。

## 功能

- 顶部 **学校标签** 一键切换（全部 / 7 校）
- **全局搜索**：姓名、中英文名、研究方向、院系、职称、简介、论文标题
- **院系 / 单位** 与 **职称** 下拉筛选（随学校联动）
- 排序：学校 / 姓名 / 职称
- 分页「加载更多」，每页 120 条

## 文件

| 文件 | 说明 |
|---|---|
| `index.html` | 自包含单页（内嵌 CSS/JS + 全部数据），双击可开，可部署 GitHub Pages |
| `data/faculty.json` | 结构化合并数据 |
| `template.html` | 页面模板（`build.py` 注入数据后生成 `index.html`） |
| `build.py` | 汇总构建脚本（读取 `sources/*.json` + 解析 USTC 网页） |
| `sources/*.json` | 各校**富化后**的规范数据（本次补简介的成果） |
| `scrape/` | 简介抓取与抽取工具（`fetch.py` / `extract.py` / `enrich_school.py`） |

## 简介补全方法

`scrape/enrich_school.py` 针对每所学校的主页结构抓取「个人简历 / 研究领域 / 研究方向」等
字段，自动抽取并做质量过滤，结果写入 `sources/<校>.json`，再回写各校仓库与 `index.html`。

```powershell
# 1) 刷新 sources/（THU 取 git HEAD）
python make_sources.py
# 2) 抓取某校缺失简介（结果写入 sources/<校>.json）
python scrape\enrich_school.py <pku|thu|nju|sjtu|fudan|ucas> [limit] [workers]
# 3) 生成汇总页 index.html
python build.py
```

数据来源：各校物理学院 / 教师主页官方公开信息，仅供学术联系参考。
