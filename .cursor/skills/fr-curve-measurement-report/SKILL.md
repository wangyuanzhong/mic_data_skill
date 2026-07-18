---
name: fr-curve-measurement-report
description: >-
  Use when writing a formal frequency-response measurement report (PDF) with
  curve figures from an existing analysis output folder that already has
  params.json and process.xlsx after fr-curve-golden-analysis. Do not use for
  selecting golden/auxiliary standards or running FR analysis.
---

# 频响测量正式报告

## Overview

你是专业电声工程师；用户也是，但不懂编程。对外用大白话。

本 Skill **只出正式报告 PDF**（含曲线图）。不算金标、不探查原始测量包。  
选标 → `fr-curve-golden-analysis`。

### 输入在哪找

选标 Skill 的产出目录与**分析根（测量数据文件夹）同级**，不在分析根里面，也不在本 Skill 目录里。

```text
父目录/
  ├── <分析根>/                 ← 原始测量（本 Skill 不读）
  └── <产品>_YYYYMMDD_HHMMSS/   ← 产出目录（报告输入/输出都在这）
        ├── params.json
        ├── process.xlsx
        ├── process.md          ← 过程日志，报告不读
        ├── figures/            ← 本 Skill 生成
        ├── report_sections/    ← 四段正文 HTML（组版输入）
        ├── report.html
        └── report.pdf
```

用户若只给了分析根路径：到**同级**找最新（或用户指定）的 `<产品>_…` 产出目录；没有就停，让用户先跑完选标。

**读：** 该产出目录的 `params.json` + `process.xlsx`（全部 sheet 可读）。  
**不读：** `process.md`、原始测量包。  
含义字典：选标侧 [../fr-curve-golden-analysis/references/data-contract.md](../fr-curve-golden-analysis/references/data-contract.md)。  
正文版式：[references/report-outline.md](references/report-outline.md)。

**输出：** 写入同一产出目录（或用户另指定目录）：`figures/` + `report.html` + `report.pdf`。

### 脚本怎么跑

脚本在**本 Skill 目录**的 `scripts/` 下（与 `SKILL.md` 同级），用该目录的绝对/相对路径调用即可。  
**不要写「仓库根」**——Skill 可能被单独拷走，不一定有仓库。

```text
# <skill> = 本 Skill 目录（…/fr-curve-measurement-report）
# <out>   = 产出目录
python <skill>/scripts/render_figures.py --params <out>/params.json

# 推荐：四段正文先写入文件，再组版（Windows/PowerShell 也稳）
# <out>/report_sections/{intro,sensitivity,curves_notes,conclusion}.html
python <skill>/scripts/compose_html.py --output-dir <out> ^
  --intro-file <out>/report_sections/intro.html ^
  --sensitivity-file <out>/report_sections/sensitivity.html ^
  --curves-notes-file <out>/report_sections/curves_notes.html ^
  --conclusion-file <out>/report_sections/conclusion.html

python <skill>/scripts/compose_pdf.py --html <out>/report.html
```

依赖：`pip install -r <skill>/scripts/requirements.txt`，首次 PDF 再 `playwright install chromium`。

## SOP

1. **定位产出目录** — 分析根同级的 `<产品>_…`；确认有 `params.json` + `process.xlsx`。  
2. **闸门** — `curve_meta.outlier_gate == confirmed` 且结论 sheet 齐全；否则停，先完成选标。  
3. **出图** — `python <skill>/scripts/render_figures.py --params <产出目录>/params.json`  
4. **填正文** — 按 `report-outline.md` 从 params/sheet 组织四段 HTML，写入 `<out>/report_sections/*.html`（数字禁止手算）。  
5. **组版** — `compose_html`（`--*-file`）→ `compose_pdf`（见上）。  
6. **短结** — 聊天报 PDF 路径、生成了哪些图（含包络分档张数）。  
7. **改格式** — 只改 `scripts/templates/report.css`、`report.html.j2` 或组版脚本，重跑组版。

## 硬规则

1. 禁止探原始测量包、禁止重跑选标脚本、禁止改写 `process.md`。  
2. 禁止手算；表与图数据来自 sheet / 出图脚本。  
3. 灵敏度只表不图。  
4. 插图顺序由组版脚本固定（奇异值→归零叠图→包络分档→金标→辅标→一致性）。  
5. 用户要改排版 → 改组版层，不重画业务曲线逻辑（除非点名改图）。  
6. **分页（强制）：**  
   - **介绍 / 灵敏度 / 结论**：整节尽量不跨页；仅当该节内容本身超过一页时才允许拆页（`.section-keep`）。  
   - **曲线节**：因图多允许节内换页（`.section-flow`）；**每张图与图名必须同一页、不可拆开**（`.figure`）。  
   - 实现落在 `templates/report.css` + `report.html.j2`；改格式时不得删掉这些约束，除非用户明确要求放松。  
7. **组版传参（强制）：** 禁止用 `python -c` 或 CLI 字符串塞带 `<>` 的 HTML（PowerShell 会吃掉尖括号）。四段正文必须先落盘，再用 `--intro-file` / `--sensitivity-file` / `--curves-notes-file` / `--conclusion-file` 传入；`--*-file` 优先于同名内联参数。
## 和选标 Skill 怎么配合

| | 选标 | 本 Skill |
|--|------|----------|
| 做 | 探查、宽表、灵敏度/奇异值/金辅标 | 出图、HTML→PDF、写正式报告 |
| 产出位置 | 与分析根**同级**的 `<产品>_时间/` | 读该目录，报告也写回该目录 |
| 读 | 原始测量 + 过程文件 | 仅该产出目录的 `params.json` + `process.xlsx` |
