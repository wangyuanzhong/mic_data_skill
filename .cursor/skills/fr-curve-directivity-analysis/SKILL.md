---
name: fr-curve-directivity-analysis
description: >-
  Use when analyzing multi-angle frequency-response (FR) measurements to
  compute per-sample angle-vs-axial delta curves and same-angle batch
  consistency, and to produce a formal directivity report (HTML/PDF) from
  those results. Input curves are distinguished by filename per angle.
  Do not use for golden/auxiliary standard selection (that is
  fr-curve-golden-analysis) or for the standard (non-directivity)
  measurement report (that is fr-curve-measurement-report).
---

# 频响指向性分析

## Overview

你是专业电声工程师；用户也是，但不懂编程。对外用大白话；电声行话可用；编程黑话翻译成人话。  
**聊天少堆内容**：细节进文件；窗口只留短结论和必要提问。

本 Skill **不读、不依赖金标**。输入是一批含轴向 + 多角度频响的测量数据（文件名区分角度），输出是每只样机各角度相对轴向的差值、同角度跨样机的一致性，以及本 Skill 内的正式报告。

**与选标（A）同批时：** 本 Skill **不依赖**金标结果，但**禁止与 A 并行**。用户同时要选标+指向性时，必须等 A（及若需要的选标报告 B）全部跑完，才开始本 Skill 步骤0。禁止「等 A 确认奇异值的空档」去推进本 Skill。详见包 [`../README.md`](../README.md)「同批多 Skill 串行铁律」。

SOP：

1. 步骤0：路径 / 产品 / 说明 / 幅度单位 / 曲线频段（默认 250–20000，不主动问）→ 建 `process.md` 骨架 + `params.json`
2. 步骤1：探查映射 → 填「探查结论」
3. 步骤1b：聊天贴「角度×文件名确认表」→ 用户确认
4. 步骤2：写 `params.json` 角度字段 → 写 `process.xlsx` 一角度一 sheet → `process.md` 记核对
5. 步骤3：跑差值/分档/一致性/聚类/峰谷脚本（只传 `--params`）→ LLM 微调分类与勾选峰谷 → 脚本改写 md 分析章 → 聊天短结
6. 步骤4：差值出图 + 走势出图 → 白话参数（含走势说明）→ 组 HTML → 转 PDF → 短结

各步如何写 `process.md`：步骤0 按 [`references/fill-00-skeleton.md`](references/fill-00-skeleton.md) 建骨架（公共部分见 [`../shared/references/fill-00-skeleton.md`](../shared/references/fill-00-skeleton.md)）；步骤1 按 [`../shared/references/fill-01-explore.md`](../shared/references/fill-01-explore.md)；步骤1b 确认表版式见 [`../shared/references/fill-angle-file-table.md`](../shared/references/fill-angle-file-table.md)；步骤2 按 [`references/fill-02-standardize.md`](references/fill-02-standardize.md)。

**铁律：**

1. `process.xlsx`：仅步骤2写各角度宽表 sheet 可依赖 LLM；其后 sheet（`delta_*` / `freq_bins_*` / `consistency_*` / `cluster_*` / `class_mean_*` / `peak_candidates_*`）必须由脚本得到。**例外**：Agent/LLM 可改 `cluster_final_<tag>`（类 id/类名）与 `peak_candidates_<tag>.selected`（见 [`references/cluster-llm-rules.md`](references/cluster-llm-rules.md)）；距离、k、类均值、峰谷频率/幅度/Q 等数值禁止手改。
2. **传参真源是** `params.json`（模板 [references/params.template.json](references/params.template.json)，基于 [`../shared/references/params.base.template.json`](../shared/references/params.base.template.json)）。`process.md` 只作过程日志，不负责传参；禁止从 md 拼命令行。
3. `process.md`：步骤0创建；步骤1/1b/2 人工填空；步骤3/4 分析章由脚本改写。禁止算完再手补分析章。
4. **用户确认角度×文件名表之前：禁止写出角度宽表，禁止进步骤3。**
5. 报告**不展示轴向曲线**；数字不读 `process.md`。
6. `envelope` 为 `null` 时：不算合格、不建 `pass_*` sheet、报告不写合格结论。
7. 闸门：0 有骨架+params → 1 有探查结论 → 1b 确认表已确认 → 2 有 params+xlsx 核对 → 3 脚本+LLM 回写后 md 章已更新 → 4 报告已出 → 短结。
8. **与选标（A）同批时禁止并行**：见 Overview；不得在 A 未全部完成前建本 Skill 产出目录或进入步骤1。

**交付物：**

| 文件 | 作用 |
| ---- | ---- |
| `params.json` | 确定性传参（脚本只读这个） |
| `process.xlsx` | 数据处理（步骤2写各角度宽表；步骤3脚本追加 `delta_*` / `freq_bins_*` / `consistency_*` / `cluster_*` / `class_mean_*` / `peak_candidates_*`；LLM 微调 `cluster_final` 与勾选 `selected`） |
| `process.md` | 过程日志（防黑盒；步骤3/4 分析章由脚本写入） |
| `figures/` | 报告用 PNG（脚本出图） |
| `report.html` / `report.pdf` | 正式报告（脚本组版） |

以上文件都在**产出目录**：与分析根同级的 `<产品>_<时间>/`（相对分析根为 `../<产品>_<时间>/`）。  
（C 产出目录与 A 选标产出目录**物理隔离**：同一批数据既选标又指向性 = 两个产出目录。）  
（params/sheet 含义字典见 [`references/data-contract-params.md`](references/data-contract-params.md) 与 [`references/data-contract-sheets.md`](references/data-contract-sheets.md)。）

聊天用于互动与短结，不是正式报告。

## 步骤 0：Intake

目标：收齐开工信息；创建 `process.md` 骨架与 `params.json`。

按 **先收信息 → 写文件** 执行。

### 先收信息

公共项处理见 [`../shared/references/fill-00-skeleton.md`](../shared/references/fill-00-skeleton.md)。C 专有：

| 项 | 怎么处理 |
|----|----------|
| 曲线分析下限 Hz | **强制不许问**；默认 250；用户主动提才改 |
| 曲线分析上限 Hz | **强制不许问**；默认 20000；用户主动提才改 |
| 命名 / 角度说明 | 用户主动给就记；没有 → 步骤1 探查后请其确认 |
| 关注频点 | 默认 `[1000]`；主动问"默认关注 1000Hz 差值，要不要加其他频点？" → 写入 `params.focus_freqs` |

### 写文件

**产出目录（强制）：** 建在与「分析根目录」**同级**（同一父目录下），目录名 `<产品>_<YYYYMMDD_HHMMSS>`。  
禁止建在本仓库 / skill 下的 `output/`。

必问项收齐后，在该产出目录：

1. 按 [`references/fill-00-skeleton.md`](references/fill-00-skeleton.md) **创建** `process.md`
2. 复制 [`references/params.template.json`](references/params.template.json) → `params.json`，填入本步已收齐字段（`product` / `note` / `data_root` / `output_dir` / `unit` / `f_lo_hz` / `f_hi_hz`）。`angles` / `axial_angle` / `sample_count` 暂留模板默认（待步骤2 填）；`envelope` 保持 `null`

硬规则：缺必问项，或尚未创建 `process.md` 与 `params.json` → 不进步骤1。缺什么问什么。

## 步骤 1：探查与映射

目标：弄清频率/幅度/样机/角度怎么切；高置信度少打扰；探查结论写入 `process.md`。

按 [`../shared/references/fill-01-explore.md`](../shared/references/fill-01-explore.md) 执行。C 专有切分维度：在「样机」之上再切「角度」（文件名 / 列名 / 区域标题等），并标出哪一角是**轴向参考**（不写死必须叫 0° / axis；以本批映射确认为准）。

### 1.3 硬规则

1. 高置信度：聊天不堆表；`process.md` 仍要有探查结论 + 映射摘要表。
2. 中/低未确认前：不进入标准化/跑脚本。
3. **「探查结论」未写入** `process.md` **之前，禁止创建** `process.xlsx`**。**
4. 映射就绪 → 进入步骤1b。

## 步骤 1b：角度×文件名确认

目标：在写角度宽表前，用固定格式表请用户确认角度与文件名映射。

按 [`../shared/references/fill-angle-file-table.md`](../shared/references/fill-angle-file-table.md) 在聊天贴表：

- 列头 = 角度（含轴向）
- 行 = 序号，单元格 = 文件名

确认时若发现不自然处（缺格、错位、同序号文件名对不上、某角度样机数与轴向不一致、疑似映射反了、序号重复/不连续），**必须主动提出**。

**硬规则：用户确认前，禁止写出角度宽表，禁止进步骤2 末与步骤3。**

## 步骤 2：标准化 + 入参

目标：更新 `params.json`（真源）；写出 `process.xlsx` 一角度一 sheet；`process.md` 记核对。  
顺序：**2.1 写 params → 2.2 写 xlsx → 2.3 md 核对**。

### 2.0 前提

`process.md` 与 `params.json` 已存在，且「探查结论」已填、确认表已获用户确认。否则先回步骤0/1/1b，**不要先建 process.xlsx**。

### 2.1 先写 params.json

写入输出目录 `params.json`：

- `angles`：有序角度标签列表（含轴向；顺序以确认表列头为准）
- `axial_angle`：确认表里指定的轴向角度标签
- `sample_count`：序号个数
- `envelope`：保持 `null`（本 plan 不做包络合格）
- `unit` / `f_lo_hz` / `f_hi_hz`：与步骤0一致

再按 [`references/fill-02-standardize.md`](references/fill-02-standardize.md) 把「入参见 params.json」写入 `process.md`（仅日志，不抄命令行表）。

### 2.2 再写 process.xlsx 角度宽表

Agent **只在这一步**写出角度宽表；分析 sheet（`delta_*` / `consistency_*`）留给脚本，不要手建。

创建/覆盖 `process.xlsx`，**每个角度一张 sheet**，sheet 名 = 角度标签规范化（去 `°` / `deg`，仅 `[A-Za-z0-9_]`，见脚本 `normalize_angle_tag`）：

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（纵轴，自上而下）；A1 可为 `freq_hz` 或空 |
| 第 1 行 B 列起 | 样机名（按序号顺序） |
| B2 起 | 该频率下该样机的幅度 dB |

各角度 sheet **同序号同列位**；频率列（A 列）一致。频率网格不一致时先对齐到统一频率列，并在本步 md 里写明做法。聊天只报：sheet 数、各 sheet 行列数、样机数。

### 2.3 立刻把核对写入 process.md

xlsx 一写完，按 [`references/fill-02-standardize.md`](references/fill-02-standardize.md) 补「标准化说明 + 核对」。对不上 → 先修宽表再往下。

### 2.4 硬规则

1. 顺序：确认表 → params → xlsx → md 核对；禁止只丢 xlsx、params 未更新就进步骤3。
2. 本步不跑差值/一致性脚本。

## 步骤 3：运行脚本

### 前提（未齐则退回步骤2）

1. `process.xlsx` 里已有与 `params.angles` 同名的各角度 sheet。
2. `params.json` 中 `angles` / `axial_angle` / `sample_count` 已写好。
3. 本步数字只准来自脚本写出的 sheet / 脚本写入的 md。

执行顺序：**3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7 → 3.8**。

### 3.1 差值

跑

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_deltas.py --params <与分析根同级的产出目录>/params.json
```

脚本对每个非轴向角度，按列位对轴向求差，写出 `delta_<tag>` sheet。列数不一致 → 非零退出，不写半成品。

### 3.2 频点分档

跑

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py --params <产出目录>/params.json
```

脚本读 `delta_<tag>` sheet，对 `params.focus_freqs` 每个频点找最近频率，按 1dB 一档统计各角度差值分布，写出 `freq_bins_<tag>`（明细）与 `freq_bins_summary_<tag>`（统计）两张 sheet/角度。跑后自检失败 → 删坏 sheet + exit 3。

`focus_freqs=[]` → 合法跳过，不写 sheet。`focus_freqs` 非空但 `delta_*` sheet 缺失 → exit 2。

### 3.3 一致性

跑

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_consistency.py --params <与分析根同级的产出目录>/params.json
```

脚本读 `delta_*` sheet，按同角度跨样机算逐频点 `std_db` / `width_db` 等，写出 `consistency_<tag>` 与 `consistency_summary`。

### 3.4 走势分类

跑

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_cluster.py --params <产出目录>/params.json
```

脚本对每个非轴向角度：读 `delta_<tag>`，写 `cluster_dist_<tag>` / `cluster_suggest_<tag>` / `cluster_meta_<tag>`；若无 `cluster_final_<tag>` 则从 suggest 复制。重跑 cluster **不覆盖**已有 final。L2 自检失败 → 删坏 sheet + exit 3。

### 3.5 Agent/LLM 微调分类

按 [`references/cluster-llm-rules.md`](references/cluster-llm-rules.md) **只改** `cluster_final_<tag>`（`cluster_id` / `cluster_name`）；禁止改 dist/suggest/meta 数值。允许命名、合并类、离群单独成类；不强制 askuser。若改动与距离矩阵矛盾 → 在 `process.md` 记理由。

### 3.6 类均值峰谷候选

跑

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_peaks.py --params <产出目录>/params.json
```

脚本读 `cluster_final_<tag>` + `delta_<tag>`，写 `class_mean_<tag>` + `peak_candidates_<tag>`（`selected` 初值全 `no`）。缺 final → exit 2。L2 自检失败 → exit 3。

### 3.7 Agent/LLM 勾选峰谷

按 [`references/cluster-llm-rules.md`](references/cluster-llm-rules.md) **只改** `peak_candidates_<tag>.selected`（`yes`/`no`）；禁止改 freq/amplitude/q/prominence。只勾肉眼明显的峰谷；报告与出图只读 `selected=yes`。

### 3.8 聊天短结（必做）

分析章都已由脚本写入、分类与峰谷已勾选后，按 [`references/fill-chat-summary.md`](references/fill-chat-summary.md) 在聊天贴短结。缺任一项 → 本步未完成。

### 硬规则

1. 必须按 3.1 → … → 3.8；禁止连跑完再一次性手补 md。
2. 命令行只带 `--params …`（3.5/3.7 为 LLM 回写 xlsx，不跑脚本）。
3. 无对应 sheet，不得填假结论。
4. `envelope=null` 时，禁止写合格/不合格。
5. 脚本 exit 2/3 → 向用户说明并询问是否重跑/改 params；禁止静默跳过。

## 步骤 4：正式报告

目标：在产出目录出 `report.html` → `report.pdf`（含图，**不展示轴向曲线**）。

### 4.1 出图

先跑差值/一致性图：

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/render_figures.py --params <产出目录>/params.json
```

产出 `figures/` 下 PNG：每个非轴向角度一张「差值叠图_<tag>.png」；一张「一致性sigma.png」。**不生成轴向曲线图。**

再跑走势图：

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/render_trend_figures.py --params <产出目录>/params.json
```

产出 `figures/` 下 PNG：每非轴向角度 `走势_类均值_<tag>.png`（标注 selected 峰/谷）；每类 `走势_类内叠图_<tag>_类<id>.png`。缺 `cluster_final` / `peak_candidates` → exit 2。

### 4.2 准备五段白话文本参数

按 [`references/report-outline.md`](references/report-outline.md) 准备（可全部为空）：

- `--intro-note`：批次 / 产品介绍
- `--deltas-note`：差值形态说明
- `--consistency-note`：一致性观察
- `--trend-note`：走势分析观察（分类/峰谷形态）
- `--conclusion-note`：结论

要求：纯白话；不要表；不要尖括号标签（PowerShell 会把 `<>` 当重定向）。

频点差值分档节由 `compose_html.py` 从 `freq_bins_*` sheet 自动渲染（focus_freqs 非空时）；Agent 无需手写该节内容。

### 4.3 组 HTML

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/compose_html.py --output-dir <产出目录> ^
  --intro-note "……" ^
  --deltas-note "……" ^
  --consistency-note "……" ^
  --trend-note "……" ^
  --conclusion-note "……"
```

脚本：把五段 note 写入 `report_sections/`、从 sheet 生成表（含走势分析节）、插图、写出 `report.html`。  
**禁止**手写 `report.html` 或手建 `report_sections/`。

### 4.4 转 PDF

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/compose_pdf.py --html <产出目录>/report.html
```

首次若缺浏览器内核：`playwright install chromium`。

### 4.5 短结与自检

按 [`references/fill-chat-summary.md`](references/fill-chat-summary.md) 贴短结，并按 [`references/report-outline.md`](references/report-outline.md) 的「自检」核对。

### 硬规则

1. 必须先完成 4.1（两套出图脚本跑完，`figures/` 非空），再跑 4.3。
2. 改排版：只改本 Skill 的 `scripts/templates/` 与/或组版脚本，然后从 4.3 起重跑。
3. 报告不展示轴向曲线；`envelope=null` 时不写合格结论。

## 步骤 5：改格式（仅用户要求时）

只修改本 Skill 的：

- `scripts/templates/report.css`
- 和/或 `scripts/templates/report.html.j2`
- 或组版相关脚本（`scripts/compose_html.py` / `scripts/compose_pdf.py`）

然后从步骤4 的 4.3 起重跑。非用户点名，不改 `scripts/render_figures.py` 的出图业务逻辑。
