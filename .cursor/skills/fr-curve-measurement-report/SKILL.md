---
name: fr-curve-measurement-report
description: >-
  Use when writing a formal frequency-response measurement report (PDF) with
  curve figures from an existing analysis output folder that already has
  params.json and process.xlsx after fr-curve-golden-analysis. Do not use for
  selecting golden/auxiliary standards or running FR analysis.
compatibility: >-
  Requires Python 3.10+ with openpyxl, matplotlib, jinja2, and playwright
  (run "playwright install chromium" once before generating report.pdf).
license: Proprietary. See repository LICENSE for internal/private-use terms.
---

# 频响测量正式报告

## Overview

你是专业电声工程师；用户也是，但不懂编程。对外用大白话。

本 Skill **只出正式 PDF 报告**（含曲线图）。  
**不做：** 探查原始测量、算金标、改选标产出目录里的 `process.md`、重跑选标脚本（那是 `fr-curve-golden-analysis`）。

开工前提：选标已完成，有**产出目录**（含已确认的 `params.json` + `process.xlsx`）。

### SOP（总览）

1. **步骤0** 定位产出目录（下文记为「产出目录」；找不到就问用户绝对路径）
2. **步骤1** 闸门：只读 `data-contract-curve-meta.md` + `data-contract-report-quickref.md`，再核对 `process.xlsx`
3. **步骤2** 调用本 Skill 的 `scripts/render_figures.py` 出图
4. **步骤3** 组版：准备白话时按需读 `report-outline` / 对应 `data-contract-*.md` → 跑 `scripts/compose_html.py` → 再跑 `scripts/compose_pdf.py`
5. **步骤4** 短结；按 `references/report-outline.md` 的「自检」全表核对
6. （仅用户要改排版时）改 `scripts/templates/` 下模板后重跑步骤3

### Overview 铁律

1. 禁止探原始测量包；禁止重跑选标；禁止改写产出目录里的 `process.md`。
2. 禁止手算；报告数字只来自产出目录的 `params.json`、`process.xlsx`，以及本 Skill 脚本写入产出目录的结果。
3. **references 按需读、不要通读。** 每个步骤只打开该步点名的合同文件；禁止把全部 `data-contract-*.md` 当开局必读。
4. 灵敏度只表不图。
5. **不要手写报告文件。** 不要手建/手改产出目录下的 `report_sections/`，不要手写表，不要手拼 `report.html`。白话只作为 `scripts/compose_html.py` 的命令行参数传入；四个 note 文件与三张表均由该脚本生成。
6. **禁止手写下列三张表**（只能出现在组版结果 `report.html` 里）：介绍字段表、灵敏度明细、灵敏度分档计数。

---

## 步骤 0：定位产出目录

目标：确认选标产出目录的**绝对路径**（下文凡写「产出目录」均指此路径）。

### 长什么样

与「分析根」（原始测量文件夹）**同级**，目录名常为 `<产品>_YYYYMMDD_HHMMSS`，且其中必须已有：

- `params.json`
- `process.xlsx`

（可有 `process.md`；本 Skill **不读** `process.md`。）

### 怎么找

1. 用户已给出产出目录绝对路径 → 直接用。
2. 用户只给了分析根 → 到其**同级**目录中找最新或用户点名的 `<产品>_…` 文件夹。
3. **找不到 / 拿不准 → 必须问用户**：「请给出选标产出目录的绝对路径（该文件夹内应有 params.json 与 process.xlsx）。」禁止猜路径继续。

### 本步硬规则

未确认产出目录绝对路径，或其中缺少 `params.json` / `process.xlsx` → 禁止进入后续步骤。  
本步**不需要**读 `references/`。

---

## 步骤 1：闸门

本步**只读**下面两个文件，不要打开其它 `data-contract-*.md`。

### 1.1 本步必读（仅此两文件）

1. `references/data-contract-curve-meta.md` — 理解 `outlier_gate`  
2. `references/data-contract-report-quickref.md` — 报告至少依赖哪些 sheet  

禁止只靠猜列名；禁止用产出目录里的 `process.md` 代替以上文件。

### 1.2 核对产出目录

1. 打开产出目录 `process.xlsx` 的 sheet `curve_meta`：`outlier_gate` 必须为 `confirmed`（含义见刚读的 `data-contract-curve-meta.md`）。  
2. 对照刚读的 `data-contract-report-quickref.md`，确认表中「读哪里」列涉及的结论 sheet 在 `process.xlsx` 里都存在（以该速查表为准）。  
3. 不过闸 → **停**，告知用户先完成选标侧奇异值确认；本 Skill 不代跑选标。

### 本步硬规则

- 未读 1.1 两文件 → 禁止做 1.2，禁止步骤2、步骤3。  
- 闸门不过 → 禁止步骤2、步骤3。  
- 本步**不要**打开 params / sensitivity / sheets-curves / curves-wide 等其它合同文件（留给步骤3按需打开）。

---

## 步骤 2：出图

令 **本 Skill 根目录** = 本 `SKILL.md` 所在文件夹（其下有 `scripts/`、`references/`）。  
调用脚本时使用「本 Skill 根目录」下的路径，不要写「仓库根」（Skill 可能被单独拷走）。

### 命令

```text
python <本Skill根目录>/scripts/render_figures.py --params <产出目录>/params.json
```

### 本步输出（供步骤3使用）

产出目录下的 `figures/` 文件夹中的 PNG。  
插图文件名与顺序的核对标准在步骤4自检时再读：`references/report-outline.md` → **「### C. 曲线图」**。本步出图**不必**先读该节。

### 本步硬规则

- 失败，或产出目录 `figures/` 为空 → 禁止进入步骤3。  
- 缺 Python 依赖时：先执行  
  `pip install -r <本Skill根目录>/scripts/requirements.txt`  
- 本步**不需要**读任何 `data-contract-*.md`（脚本自己读 `params.json` / `process.xlsx`）。

---

## 步骤 3：组版

按 **3.1 → 3.2 → 3.3** 顺序做，不要跳。

### 3.1 准备四段白话文本参数（可全部为空）

这四段是下一步 `scripts/compose_html.py` 的**命令行参数字符串**，不是让你先去创建文件。

**先**打开 `references/report-outline.md`，只读 **「## 传参（对应 compose 参数）」**（以及需要时的 **「## 脚本生成（Agent 勿重复）」** 第 4 点：结论勿贴整表）。

然后**按你要写的那一段**，再打开对应合同文件（不要一次打开全部）：

| 命令行参数 | 写什么 | 本段再读哪个合同文件 | 数字从产出目录哪里抄 |
|------------|--------|----------------------|----------------------|
| `--intro-note` | 介绍一两句 | `references/data-contract-params.md` | `params.json` |
| `--sensitivity-note` | 灵敏度金标是谁、为何选它等 | `references/data-contract-sheets-sensitivity.md` | sheet `sensitivity`、`sensitivity_meta` |
| `--curves-notes` | 剔除谁、曲线金标/辅标等 | `references/data-contract-curve-meta.md`、`references/data-contract-sheets-curves.md`（尤其 `curve_rank`）；可选再看 `data-contract-report-quickref.md` | sheet `curve_meta`、`curve_rank` |
| `--conclusion-note` | 结论三四句 | 同上已打开的结论合同即可；只摘句不抄整表 | 同上 |

某段省略则**不必**为该段打开对应合同。四段都空则 3.1 可不打开合同，直接 3.2。  
原始宽表 `curves` 一般不需要：仅当你要对齐底稿布局时再读 `data-contract-sheets-curves-wide.md`。

要求：纯白话；不要表；不要尖括号标签（PowerShell 会把 `<>` 当重定向）。

### 3.2 运行组版脚本 `scripts/compose_html.py`

**没有**单独的「只生成四个小 note 文件」的脚本。  
下面这一条命令由 `scripts/compose_html.py` 一次完成：

1. 把 3.1 的四段参数写入产出目录：  
   - `report_sections/intro_note.txt`  
   - `report_sections/sensitivity_note.txt`  
   - `report_sections/curves_notes.txt`  
   - `report_sections/conclusion_note.txt`  
2. 从 `params.json` / `process.xlsx` 生成介绍字段表、灵敏度明细、灵敏度分档计数（脚本行为说明见 `references/report-outline.md` → **「## 脚本生成（Agent 勿重复）」**；本步若已在 3.1 读过可不再读）  
3. 插入步骤2 产出的 `figures/` 中图片  
4. 写出产出目录下的 `report.html`

四段白话都空时：

```text
python <本Skill根目录>/scripts/compose_html.py --output-dir <产出目录>
```

有白话时（引号内换成 3.1 准备好的原文）：

```text
python <本Skill根目录>/scripts/compose_html.py --output-dir <产出目录> --intro-note "……" --sensitivity-note "……" --curves-notes "……" --conclusion-note "……"
```

**Windows / 长文本可用 `--*-note-file` 代替 `--*-note`：** 每段都有对应的 `--intro-note-file` / `--sensitivity-note-file` / `--curves-notes-file` / `--conclusion-note-file`（还各有一个别名 `--intro-file` / `--sensitivity-file` / `--conclusion-file`），把该段白话先写进一个 UTF-8 文本文件，传文件路径即可，避免把长文本或引号塞进 PowerShell 命令行。同一段若两者都传，文件优先。

**禁止**自己创建或手改产出目录下的 `report_sections/`。  
**禁止**手写介绍字段表、灵敏度明细、灵敏度分档计数。

### 3.3 运行转 PDF 脚本 `scripts/compose_pdf.py`

```text
python <本Skill根目录>/scripts/compose_pdf.py --html <产出目录>/report.html
```

成功后应得到产出目录下的 `report.pdf`。  
首次若缺浏览器内核：`playwright install chromium`。

### 本步硬规则

- 必须先完成步骤2（产出目录 `figures/` 非空），再跑 3.2。  
- 改排版：只改本 Skill 的 `scripts/templates/report.css` 与/或 `scripts/templates/report.html.j2`，然后从 3.2 重跑。  
- **分页：** 介绍/灵敏度/结论尽量整节不跨页（模板 class `.section-keep`）；曲线节可换页（`.section-flow`）；图与图名同页不拆（`.figure`）。非用户明确要求，不得删掉这些约束。

---

## 步骤 4：短结与自检

本步再打开并执行：

`references/report-outline.md` → **「## 自检（组版后、短结前；打开 `<out>/report.html` 用搜索核对）」**

按其下 **A～E** 各表逐项核对。此前步骤**不必**预读自检章。

聊天向用户报告：

- 产出目录下 `report.pdf` 的绝对路径  
- `figures/` 中包络分档图张数（文件名形如 `包络分档_正负*.png`）  
- 上述自检是否全部通过  

缺项则回到步骤2或步骤3重跑；**禁止**手写补表。

---

## 步骤 5：改格式（仅用户要求时）

只修改本 Skill 的：

- `scripts/templates/report.css`  
- 和/或 `scripts/templates/report.html.j2`  
- 或组版相关脚本（`scripts/compose_html.py` / `scripts/compose_pdf.py` 等）

然后从步骤3 的 3.2 起重跑。非用户点名，不改 `scripts/render_figures.py` 的出图业务逻辑。
