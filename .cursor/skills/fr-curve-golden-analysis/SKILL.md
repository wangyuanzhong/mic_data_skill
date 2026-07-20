---
name: fr-curve-golden-analysis
description: >-
  Use when analyzing frequency-response (FR) measurement folders to select
  curve golden/auxiliary standards, bin absolute sensitivity in 0.5dB steps,
  or run outlier review on SPL/XLS/CSV curve data. Do not use for writing the
  formal measurement report (that is fr-curve-measurement-report).
---

# 频响曲线金标分析

## Overview

你是专业电声工程师；用户也是，但不懂编程。对外用大白话；电声行话可用；编程黑话翻译成人话。  
**聊天少堆内容**：细节进文件；窗口只留短结论和必要提问。

SOP：

1. 步骤0：路径 / 产品 / 说明 / 幅度单位 / 曲线频段（可默认）→ 建 `process.md` 骨架 + `params.json`
2. 步骤1：探查映射 → 填「探查结论」
3. 步骤2：先写 `params.json` → 再写 `process.xlsx` 宽表 → `process.md` 记日志与核对
4. 步骤3：按小点跑脚本（只传 `--params`）；脚本改写 md 分析章；完后聊天短结

各步如何写`process.md`文件：各步骤按`references/fill-*.md` 填空，步骤0按`references/fill-00-skeleton.md` 建骨架

**铁律：**

1. `process.xlsx`：仅步骤2写 `curves` 宽表可依赖 LLM；其后 sheet 必须由脚本得到。
2. **传参真源是** `params.json`（模板 [references/params.template.json](references/params.template.json)）。`process.md` 只作过程日志，不负责传参；禁止从 md 拼命令行。
3. `process.md`：步骤0创建；步骤1/2 人工填空；步骤3 分析章由脚本改写。禁止算完再手补分析章。
4. 闸门：0 有骨架+params → 1 有探查结论 → 2 有 params+xlsx 核对 → 3 脚本后 md 章已更新 → 短结。
5. **与指向性（C）同批时禁止并行**：若用户同时要选标与指向性（或同时挂载两 Skill），必须先完整完成本 Skill（含步骤3奇异值确认与曲线第二阶段；若还要正式选标报告则再跑完 `fr-curve-measurement-report`），**全部结束后**才允许开始 C 步骤0。禁止两边穿插建目录/探查/写表；禁止本 Skill 卡在等确认时去推进 C。详见包 [`../README.md`](../README.md)「同批多 Skill 串行铁律」。

**交付物：**


| 文件 | 作用 |
| ---- | ---- |
| `params.json` | 确定性传参（脚本只读这个） |
| `process.xlsx` | 数据处理（步骤2写宽表；步骤3脚本追加分析 sheet） |
| `process.md` | 过程日志（防黑盒；步骤3分析章由脚本写入） |
| [references/data-contract.md](references/data-contract.md) | params + process.xlsx 各 sheet 含义（报告 Skill 只引用） |

以上三个文件都在**产出目录**：与分析根同级的 `<产品>_<时间>/`（相对分析根为 `../<产品>_<时间>/`）。


聊天用于互动与短结，不是正式报告。

## 步骤 0：Intake

目标：收齐开工信息；创建 `process.md` 骨架与 `params.json`。

按 **先收信息 → 写文件** 执行。

### 先收信息


| 项         | 怎么处理                                  |
| --------- | ------------------------------------- |
| 分析根目录     | 没有就问                                  |
| 产品名       | 没有就问；路径里能合理猜到可先给出请用户确认                |
| 说明        | **问要不要加**；不要 → 写「无」                   |
| 幅度单位      | 没有就问；文件头能合理猜到（如 dBV、dB SPL）必须先给出请用户确认 |
| 曲线分析下限 Hz | 默认 100；**必须用户确认**（可改）                    |
| 曲线分析上限 Hz | 默认 15000；**必须用户确认**（可改）                  |

- 开局确认包：按 [`../shared/references/intake-confirm.md`](../shared/references/intake-confirm.md) 执行。
- 若本对话**未**挂载指向性 Skill：必须问「本批要不要做指向性？」；答「要」视同已挂载 C（默认与串行规则见该文件）。
- 若已挂载指向性：不要在此重复问「要不要」；C 默认确认由 C 步骤0 / 同批开局确认包一并处理。

### 写文件

**产出目录（强制）：** 建在与「分析根目录」**同级**（同一父目录下），目录名 `<产品>_<YYYYMMDD_HHMMSS>`。  
禁止建在本仓库 / skill 下的 `output/`。

示例：分析根 `…/新建文件夹/20260618-MILAB capsule-CY001`  
→ 产出 `…/新建文件夹/<产品>_20260717_145247/`  
（相对分析根：`../<产品>_20260717_145247/`）

必问项收齐后，在该产出目录：

1. 按 [references/fill-00-skeleton.md](references/fill-00-skeleton.md) **创建** `process.md`
2. 复制 [references/params.template.json](references/params.template.json) → `params.json`，填入本步已收齐字段（`product` / `note` / `data_root` / `output_dir` / `unit` / `f_lo_hz` / `f_hi_hz`）。`data_root`、`output_dir` 写清上述路径；其余可先保持模板默认（`curves.exclude` 为 `null`）

硬规则：确认包未齐，或缺必问项，或尚未创建 `process.md` 与 `params.json` → 不进步骤1。缺什么问什么。

## 步骤 1：探查与映射

目标：弄清频率/幅度/样机怎么切；高置信度少打扰；探查结论写入 `process.md`。

按 **1.1 → 1.2 → 1.3** 执行。

### 1.1 探查

不管后缀，把文件当表/文本读。由大到小：

1. **按文件**列出候选
2. **按 sheet 分**（无 sheet 的文本当作 1 个 sheet）
3. **每个 sheet 再分大区域**（中间空很多行/列 → 两块区域）
4. **每个区域找频率行/列**（两区可能共用同一频率轴）
5. **再切样机**（多列幅度、多段、ID、文件名等）
6. 标置信度：`高` / `中` / `低`

**文件 → sheet → 区域 → 频率 → 样机（幅度跟着频率）**

### 1.2 写 process.md + 聊天

1. 确保 `process.md` 已由步骤0建好。
2. 打开 [references/fill-01-explore.md](references/fill-01-explore.md)，按版式填进 `## 探查结论`（勿另起文档、勿改标题）。
3. 再决定聊天里说多少：


| 置信度       | 聊天里有什么                             |
| --------- | ---------------------------------- |
| **高**     | 短版探查结论 + 一句详情在 process.md；不贴映射表/预览 |
| **中 / 低** | 探查结论 + 映射摘要表 + 预览 + 问清不确定点         |
| 用户说映射错了   | 停，改完后更新 process.md，再按上表决定聊多少       |


怎么问（仅中/低）：

- ❌ 「请问哪一列是频率？」
- ✅ 「拿不准的是：…… 请改映射摘要表，或回确认。」

### 1.3 硬规则

1. 高置信度：聊天不堆表；`process.md` 仍要有探查结论 + 映射摘要表。
2. 中/低未确认前：不进入标准化/跑脚本。
3. **「探查结论」未写入** `process.md` **之前，禁止创建** `process.xlsx`**。**
4. 映射就绪 → 进入步骤2，不要手算灵敏度。

## 步骤 2：标准化 + 入参

目标：更新 `params.json`（真源）；写出 `process.xlsx` 宽表；`process.md` 记日志与核对。  
顺序：**2.1 写 params → 2.2 写 xlsx → 2.3 md 核对**。

### 2.0 前提

`process.md` 与 `params.json` 已存在，且「探查结论」已填。否则先回步骤0/1，**不要先建 process.xlsx**。

### 2.1 先写 params.json

问中线（不要擅自默认成整批平均）：

> 1000Hz 灵敏度中线怎么定？  
> 1）按这批数据的平均值  
> 2）按你给的理论值 / 设计值（请给出数值和单位）

选 2 但没给数 → 继续问。

写入输出目录 `params.json`：

- `sensitivity.midline_mode`：`mean` 或 `value`
- `sensitivity.midline_db`：仅 `value` 时填数字，否则 `null`
- `curves.aux_count`：用户没说就用 `3`
- `curves.exclude`：保持 `null`（待步骤3确认）
- `unit` / `f_lo_hz` / `f_hi_hz`：与步骤0一致

再按 [references/fill-02-params.md](references/fill-02-params.md) 把「入参见 params.json」写入 `process.md`（仅日志，不抄命令行表）。

### 2.2 再写 process.xlsx 宽表

Agent **只在这一步**写出宽表；分析 sheet 留给脚本，不要手建。

创建/覆盖 `process.xlsx`，sheet 名用 `curves`：


| 位置         | 内容                                |
| ---------- | --------------------------------- |
| A 列        | 频率 Hz（纵轴，自上而下）；A1 可为 `freq_hz` 或空 |
| 第 1 行 B 列起 | 样机名（规则见下）                         |
| B2 起       | 该频率下该样机的幅度 dB                     |


样机名（按**每个源文件**判断）：

```text
如果 该源文件里只有 1 条曲线：
    样机名 = 文件名（去掉后缀）
否则（该源文件里有多条曲线）：
    样机名 = 原始表里头的名字（列名 / sheet 内标注 / 区域标题等，以映射摘要为准）
```

频率网格不一致时先对齐到统一频率列，并在本步 md 里写明做法。聊天只报：已生成、几行几列、几个样机。

### 2.3 立刻把核对写入 [process.md](http://process.md)

xlsx 一写完，按同一 [references/fill-02-params.md](references/fill-02-params.md) 补「标准化说明 + 核对」。对不上 → 先修宽表再往下。

### 2.4 硬规则

1. 顺序：params → xlsx → md 核对；禁止只丢 xlsx、params 未更新就进步骤3。
2. 本步不跑分析脚本。

## 步骤 3：运行脚本

### 前提（未齐则退回步骤2）

1. `process.xlsx` 里已有名为 `curves` 的 sheet。
2. `params.json` 中线等字段已写好；`curves.exclude` 在 3.2 前为 `null`。
3. 本步数字只准来自脚本写出的 sheet / 脚本写入的 md。

执行顺序：**3.1 → 3.2 → 用户确认 → 3.3 → 3.4**。

### 3.1 灵敏度

跑

```text
python .cursor/skills/fr-curve-golden-analysis/scripts/run_sensitivity.py --params <与分析根同级的产出目录>/params.json
```

### 3.2 曲线第一阶段（奇异值提名）

此时 `params.json` 里 `curves.exclude` 必须仍是 `null`。

跑

```text
python .cursor/skills/fr-curve-golden-analysis/scripts/run_curves.py --params <与分析根同级的产出目录>/params.json
```

**聊天：** 短说建议剔除与高Q豁免，请用户选：不剔除 / 按建议剔除 / 自定义名单。  
**未确认前：禁止进入 3.3，禁止写曲线金标或辅标。**

### 3.3 曲线第二阶段（确认后排名）

用户确认后，先改产出目录 `params.json` 的 `curves.exclude`：

- 不剔除 → `"exclude": []`
- 按建议或自定义剔除 → `"exclude": ["样机A", "样机B"]`（名单以用户确认为准）

再跑：

```text
python .cursor/skills/fr-curve-golden-analysis/scripts/run_curves.py --params <与分析根同级的产出目录>/params.json
```

### 3.4 聊天短结（必做）

三章都已由脚本写入后，按 [references/fill-35-chat-summary.md](references/fill-35-chat-summary.md) 在聊天贴短结。缺任一项 → 本步未完成。

### 硬规则

1. 必须按 3.1 → 3.2 → 确认并改 params → 3.3 → 3.4；禁止连跑完再一次性手补 md。
2. 命令行只带 `--params …`。
3. 无对应 sheet，不得填假结论。
4. `outlier_gate=pending` 时，禁止写曲线金标/辅标。

