# Design: 频响测量正式报告 Skill（fr-curve-measurement-report）

**日期:** 2026-07-17  
**状态:** 设计已定稿（输入合同、七类图、四段正文、HTML→PDF 组版）；实现期再补脚本命令与 data-contract 全文  
**仓库:** `mic_data_skill`  
**Skill 路径:** `.cursor/skills/fr-curve-measurement-report/`  
**上游 Skill:** `fr-curve-golden-analysis`（只消费其产出，不代劳选标）

---

## 1. 目标

对**已经分析完成**的产出目录，生成一产品一份正式报告：

1. 脚本出齐规定曲线图（含张数可变的包络分档图）  
2. Agent 按四段结构填正文（大白话）  
3. 组版代码将 HTML 自适应排成 **PDF**；用户改格式时改组版层，不重算分析  

**不是**选金标/探原始测量包；那是选标 Skill 的事。

---

## 2. 总体分工与产物

| 层 | 谁做 | 产出 |
|----|------|------|
| 含义合同 | 选标 Skill `references/` | `params.json` 字段 + 各 sheet 含义（报告只引用） |
| 出图 | 报告 Skill **脚本** | `figures/` 下中文文件名 PNG |
| 组版 | 报告 Skill **组版代码** + Agent | `report.html` → `report.pdf` |
| 正文 | Agent 按版式填 | 介绍 → 灵敏度 → 曲线（插图）→ 结论 |

**输入（必须）：** 产出目录下的 `params.json` + `process.xlsx`（**全部 sheet 可读**）。  
**不读：** `process.md`。  
**禁止：** 重探原始测量包、重跑选标脚本、手算数字、在缺前置条件时假装出报告。

**产物位置：** 默认与分析产出同目录（或用户指定目录）：`figures/` + `report.html` + `report.pdf`。

---

## 3. 输入合同

### 3.1 真源

| 文件 | 角色 |
|------|------|
| `params.json` | 产品、说明、单位、分析频段、中线、剔除名单、辅标个数等元信息 |
| `process.xlsx` | 数字与曲线真源；报告出图/列表可读取其中任意 sheet |

含义目录单开为选标侧 reference（计划名 `data-contract.md`）：逐字段、逐 sheet 写清用途。报告 `SKILL.md` **只链接引用，不维护第二份字典**。

### 3.2 闸门（未过则停）

1. 产出目录存在 `params.json` 与 `process.xlsx`  
2. `curve_meta` 中 `outlier_gate == confirmed`  
3. 至少可读：`sensitivity`、`sensitivity_meta`、`curve_rank`、`curve_mean_before_outlier`、`curve_mean_after_outlier`、`outlier_decision`、`curve_step1_leveled`（及出图所需偏差类 sheet）  
4. 出图脚本成功后，再组 PDF  

---

## 4. 画幅与分析框（全局）

- **横轴画满数据：** 频率上下限 = 数据宽表中实际存在的 min～max Hz，**不按**分析频段裁切曲线。  
- **框跟 json：** 分析频段框、包络有效范围、一致性 σ 的计算频段等「框内逻辑」使用 `params.json` 的 `f_lo_hz`–`f_hi_hz`。  

灵敏度：**只列表，不出图**。

---

## 5. 七类图（内容、sheet、中文命名、插图顺序）

共性数据：

- 1 kHz 归零序列：`curve_step1_leveled`  
- 剔异后均值：`curve_mean_after_outlier`  
- 剔异前均值（奇异值图用）：`curve_mean_before_outlier`  
- 分档/角色：`curve_rank` / `curve_step4_envelope`（与选标同一套 `max_abs → δ`，δ 为 0.1 dB 向上取整）  

### 5.1 插图顺序（正文曲线节固定为此序）

**3 → 2 → 1 → 4 → 5 → 6 → 7**（下表「逻辑编号」为需求讨论时的编号，便于对照）

| 插图序 | 逻辑# | 内容 | 主要 sheet | 中文文件名 |
|--------|-------|------|------------|------------|
| 1 | 3 | 已剔除奇异值样机的归零绝对曲线 + 算奇异值时的均值（mean_before），叠放 | `curve_step1_leveled`、`outlier_decision`、`curve_mean_before_outlier` | `奇异值与剔异前均值.png` |
| 2 | 2 | 剔异后保留样机，1 kHz 归零绝对叠图 | `curve_step1_leveled`、`outlier_decision`（`in_mean_after=yes`） | `剔异后归零叠图.png` |
| 3 | 1 | 按最紧 δ 按 **0.5 dB 包络壳**分图：壳内样机「归零−均值」差曲线叠放；粗红线画该档 ±包络；**每壳一张**（空壳不生成） | `curve_rank` / `curve_step4_envelope`、`curve_step3_dev`（或 leveled−mean_after） | `包络分档_正负0.5dB.png`、`包络分档_正负1.0dB.png`、… |
| 4 | 4 | 金标绝对曲线 + 金标减均值曲线，同图两线 | golden 名单 + leveled + mean_after | `金标绝对与偏差.png` |
| 5 | 5 | 辅标减均值差曲线叠图 | aux 名单 + 偏差序列 | `辅标偏差叠图.png` |
| 6 | 6 | 辅标 1 kHz 归零绝对叠图 | aux + leveled | `辅标绝对叠图.png` |
| 7 | 7 | 批量一致性 σ(f)；算法与样式对齐 bk-tool（`σ(f)=std_i(A_i−μ)`）；计算在 json 频段内；横轴仍画满数据范围 | 保留样机 leveled；脚本内计算（可移植 bk-tool `curve_consistency_core` 思路） | `批量一致性sigma.png` |

### 5.2 包络分档规则（逻辑#1）

- 与选标同一指标链：带内相对 mean_after 的 `max_abs`，再收成最紧 `δ`（0.1 dB 步进）。  
- 出图按 0.5 dB 壳归堆：δ≤0.5；0.5&lt;δ≤1.0；1.0&lt;δ≤1.5；…  
- 组版扫描 `包络分档_*.png`，按档位数值排序后按序插入（张数随批次变化）。  

### 5.3 一致性图（逻辑#7）

参考 `E:\vibe\bk-tool (2)\bk-tool` 启发式一致性：公共频点上相对批次均值的样本标准差曲线；样式对齐其 σ 图（含坐标、填充、热点等视觉约定）。本项目频段取 `params` 分析范围，不强制 20–20000。

---

## 6. 正文四段结构

1. **整体介绍** — 型号、说明、分析频率范围、目标灵敏度等（`params.json` 已有字段）；短、大白话；可用表。  
2. **灵敏度** — 金标挑选与整体分档/一致性；表来自 `sensitivity` / `sensitivity_meta`；无图。  
3. **曲线** — 按分析叙述顺序写，插图严格按 §5.1；每图下可 1～2 句读图说明。  
4. **结论** — 短总结，大白话。  

版式细节放在报告 Skill `references/report-outline.md`。

---

## 7. HTML → PDF 组版

**选定方案：** 脚本出图 + Agent 填内容 + **组版代码**生成 HTML 再渲染 PDF。

```
scripts 出 figures/*.png
  → 组版生成 report.html（内容槽位 + 自适应排图）
  → 渲染 report.pdf
```

**组版代码必须可改（满足用户改格式）：**

- 多图换行、分页、避免标题孤行、表/图宽度自适应  
- 包络分档图数量不确定时按实际文件插入  
- 用户要求改版式 → 改组版脚本 / CSS / 模板；**不**重跑选标、**不**手改分析数字  

渲染工具实现期选定（如 Playwright 或 Weasyprint）；缺图或闸门失败则停止并说明原因。

纯 Markdown→Pandoc 或纯 reportlab 直接画 PDF：**不采用**（自适应与改格式成本更高）。

---

## 8. Skill 目录规划

`.cursor/skills/fr-curve-measurement-report/`

| 路径 | 作用 |
|------|------|
| `SKILL.md` | SOP：闸门 → 出图 → 组 HTML/PDF → 填四段 → 聊天短结 |
| `references/report-outline.md` | 正文版式与语气 |
| `scripts/render_figures.py`（名可微调） | 七类图 |
| `scripts/compose_pdf.py`（名可微调） | HTML 组版 + PDF |
| `scripts/` 下 CSS/模板 | 自适应排版 |

选标侧新增：`fr-curve-golden-analysis/references/data-contract.md`（params + sheets 含义全文）。

---

## 9. 与选标 Skill 边界

| | `fr-curve-golden-analysis` | `fr-curve-measurement-report` |
|--|----------------------------|-------------------------------|
| 做 | 探查、宽表、灵敏度/奇异值/金辅标、`process.xlsx` + `params.json` + 过程 md | 出图、组 PDF、写正式报告 |
| 不做 | 正式 `report.pdf` / 报告业务图 | 探原始包、改写 `process.md`、重跑选标脚本 |
| 读 | 原始测量 + 自产过程文件 | 仅 `params.json` + `process.xlsx` |

现有报告 stub 中「必读 process.md」的约定以本设计为准废止。

---

## 10. 实现期范围（本设计之后）

1. 写全 `data-contract.md`（与当前脚本 sheet 列对齐）  
2. 实现 `render_figures`（含包络分档与 σ 图）  
3. 实现 `compose_pdf` + 默认 CSS/模板  
4. 补齐 `SKILL.md` SOP 与 `report-outline.md`  
5. 用真实产出目录做一轮端到端验证  

样例测量数据不进本仓库（与选标设计一致）。

---

## 11. 决策摘要

| 决策 | 结论 |
|------|------|
| 报告素材 | `params.json` + `process.xlsx`；不读 `process.md` |
| sheet 可读性 | 全部可读（出图需要哪张读哪张） |
| 含义目录 | 选标 `references` 单开；报告只引用 |
| 出图 vs 正文 | 脚本出图；Agent 填报告 |
| 最终格式 | PDF（HTML 中间稿 + 组版代码自适应） |
| 改格式 | 改组版代码/CSS/模板 |
| 灵敏度 | 只表不图 |
| 画幅 | 数据全频段；框用 json 频段 |
| 插图序 | 3→2→1→4→5→6→7 |
| 图文件名 | 中文（见 §5.1） |
| 包络分档 | 与选标同一 `max_abs→δ`；0.5 dB 壳出图 |
| 一致性 | 对齐 bk-tool σ 算法与样式；频段用 params |
