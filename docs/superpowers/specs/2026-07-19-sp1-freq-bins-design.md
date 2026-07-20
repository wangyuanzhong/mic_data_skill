# Design: SP1 — C 频点差值分档

**日期:** 2026-07-19
**状态:** 设计已定稿（brainstorming）；实现计划见后续 writing-plans
**仓库:** `mic_data_skill`
**范围:** 仅 C（`fr-curve-directivity-analysis`）；A/B/shared 不动

---

## 1. 目标与非目标

### 1.1 目标

给 C 加"频点差值分档"能力：对用户关注的频点（默认 1000Hz，可加），按 1dB 一档统计各角度差值曲线（angle − axial）的分布。

- intake 主动问关注频点
- 脚本算分档 + 计数，写 xlsx
- 报告渲染分档表（每角度两张：明细 + 统计）
- 机械验证：脚本跑后自检产出，失败强制 askuser

### 1.2 非目标

- ❌ 包络框、pass/fail 判定、合格结论（已撤销，不在 SP1）
- ❌ 走势分析、分类、共振峰（属 SP3）
- ❌ 改 A/B 任何文件
- ❌ 改 C 现有脚本（`run_deltas` / `run_consistency` / `render_figures`）
- ❌ 改 shared
- ❌ 给现有脚本补机械验证（SP1 只给新脚本加；现有脚本未来另开任务）
- ❌ 解决"axial 被标准化两遍"问题（已决定不改，SOP 简单优先）

---

## 2. 架构与数据流

新增一个 SOP 子步（插在 `run_deltas` 之后、`run_consistency` 之前）：

```
intake（加问 focus_freqs，默认 [1000]）
  → 步骤2 标准化（不变）
  → 步骤3a run_deltas（已有，不变）
  → 步骤3b run_freq_bins（新增）← SP1 核心
  → 步骤3c run_consistency（已有，编号顺移）
  → 步骤4 报告（compose_html 加一节）
```

数据流（死命令：一切数值计算以脚本对 xlsx 处理的结果为准）：

```
params.json (focus_freqs)
   ↓
run_freq_bins.py
   ↓ 读 delta_<angle> sheet（已有）
   ↓ 算 1dB 分档 + 计数
   ↓ 写 freq_bins_<angle> + freq_bins_summary_<angle>
   ↓ 读回自检（L2 机械验证）
   ↓
process.xlsx
   ↓
compose_html.py
   ↓ 只读 xlsx 渲染（不算数）
   ↓ 写 report.html + L3 自检
   ↓
compose_pdf.py → report.pdf
```

---

## 3. params schema

新增字段：

```json
{
  "focus_freqs": [1000]
}
```

- 类型：数字数组（Hz）
- 默认：`[1000]`
- 空数组 `[]` = 合法跳过（不跑 `run_freq_bins`，报告无分档节）
- 加到 C 的 `params.template.json`
- intake 时主动问："默认关注 1000Hz 差值，要不要加其他频点？"

---

## 4. xlsx 新增 sheet

### 4.1 `freq_bins_<angle>`（明细表，每角度一张）

例：`freq_bins_135`，focus_freqs = [1000, 4000]

| 样机 | 1000Hz差值 | 1000Hz档位 | 4000Hz差值 | 4000Hz档位 |
|------|-----------|-----------|-----------|-----------|
| CY00101 | -1.5 | -2~-1 | -4.2 | -5~-4 |
| CY00102 | 0.3 | 0~1 | -0.8 | -1~0 |

- 列数 = 1（样机）+ 2 × len(focus_freqs)
- 行数 = 1（表头）+ sample_count
- 档位格式：`"lower~upper"`，1dB 一档，左闭右开
- 差值为 None：差值列空，档位列写 `N/A`

### 4.2 `freq_bins_summary_<angle>`（统计表，每角度一张）

例：`freq_bins_summary_135`，focus_freqs = [1000, 4000]

| 1000Hz分组 | 1000Hz每组数量 | 4000Hz分组 | 4000Hz每组数量 |
|-----------|---------------|-----------|---------------|
| -3~-2 | 2 | -5~-4 | 1 |
| -2~-1 | 5 | -4~-3 | 3 |
| -1~0 | 4 | -3~-2 | 5 |
| 0~1 | 3 | -2~-1 | 4 |
| | | 0~1 | 1 |

- 无左表头（A1 = 第一个频点的"分组"标题）
- 各频点独立分档（floor(min) ~ ceil(max) 跨样机）
- 频点间 bin 数不同时，短的列下方留空
- 列数 = 2 × len(focus_freqs)

### 4.3 不动的 sheet

`axis` / `135` / `180` / `delta_*` / `consistency_*` 结构不变。

---

## 5. run_freq_bins.py 脚本逻辑

### 5.1 命令行

```
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py --params <产出目录>/params.json
```

只传 `--params`（对齐现有脚本约定）。

### 5.2 前置硬 gate（exit 2）

1. `params.json` 存在且含 `focus_freqs` 字段
2. `focus_freqs` 输入校验：数组、元素为数值、> 0、无重复；非法（含重复）→ exit 2
3. `process.xlsx` 存在
4. 对每个非轴向角度：`delta_<angle>` sheet 存在
5. `focus_freqs` 为空数组 `[]` → exit 0，不写 sheet（合法跳过）
6. `focus_freqs` 非空但全部超分析频段被跳过 → exit 0 + warning（不写 sheet，不算失败）

### 5.3 核心逻辑

对每个非轴向角度 angle：
- 读 `delta_<angle>` sheet → (freqs, samples, columns)
- 对每个 focus_freq ff：
  - 找最近频点（argmin |freqs - ff|，tie 取较低频）
  - 若超出 `[f_lo, f_hi]` 分析频段（来自 `params.json`，与 `run_deltas` 同源）→ 跳过该频点 + warning
  - 取各样本在该频点的 delta（含 None）
  - 算 bin 范围：`floor(min(present)) ~ ceil(max(present))`
    - 边界：若 `floor(min) == ceil(max)`（所有 present delta 同值），强制用 `[floor(min), floor(min)+1)`
  - 每样本分档：`floor(d) ~ floor(d)+1`；None → "N/A"
- 写 `freq_bins_<angle>`（明细表）
- 写 `freq_bins_summary_<angle>`（统计表）
- L2 读回自检（见 §6）
- 自检失败 → 删刚写的 sheet → exit 3
- 自检通过 → print "VERIFICATION OK: ..."

保存 process.xlsx。

### 5.4 关键约定

- 最近频点匹配：脚本内做，不靠 LLM
- 分档边界：左闭右开 `[lo, lo+1)`，`floor(d)` 取下界
- 档位标签：`f"{lo}~{hi}"`，无 `+` 号，负号保留
- 幂等：重跑覆盖已有 `freq_bins_*` sheet
- 不读 process.md，不写 process.md（per SP2 撤销决定）

---

## 6. 机械验证（L2 跑后自检 + L3 报告自检）

### 6.1 L2 run_freq_bins.py 跑后自检

写完 sheet 后读回验证（全机械）。失败 → 删刚写的 sheet → exit 3。

验证清单（每角度）：

1. sheet 存在
2. 明细表列数 == 1 + 2 × len(focus_freqs)
3. 明细表行数 == 1 + sample_count
4. 明细表第1列样机名与 delta_<angle> 一致（顺序+内容）
5. 档位格格式：匹配 `^-?\d+~-?\d+$` 或 == "N/A"
6. 每个非 N/A 档位 lower+1 == upper
7. 统计表列数 == 2 × len(focus_freqs)
8. 统计表无左表头（A1 = 频点"分组"标题，非行标签）
9. 每频点"每组数量"列求和 == 该频点非 None delta 数（N/A 样本不计入求和）
10. 统计表"分组"标签 ⊆ 明细表档位标签
11. 所有 focus_freqs 都有对应列（或被跳过且有 warning）

全过 → print "VERIFICATION OK: <angles> angles × 2 sheets, <samples> samples, <freqs> freq points"

### 6.2 L3 compose_html.py 报告自检

写完 report.html 后读回验证（focus_freqs 非空时）：

1. report.html 含"频点差值分档"节标题
2. 每个非轴向角度有 2 张表
3. 明细表列数 == 1 + 2 × len(focus_freqs)
4. 统计表列数 == 2 × len(focus_freqs)

失败 → print "REPORT VERIFICATION FAIL: <check>" → exit 3（不删 report.html，让用户看哪里错了）

### 6.3 强制 askuser 机制（机械阻断）

验证失败时**不靠 Agent 自觉**，靠下游机械阻断逼出 askuser：

1. run_freq_bins 验证失败 → 删坏 sheet + exit 3 → xlsx 无 freq_bins sheet
2. Agent 若想跳过出报告 → compose_html 发现 focus_freqs 非空但 sheet 不存在 → exit 2
3. Agent 被迫面对：修 params 重跑 / 查 delta 数据 / 显式设 focus_freqs=[] 放弃 / abort
4. 无论哪条路，都必须用户决策——Agent 没有"假装没事继续"的选项

compose_html 改逻辑：
- focus_freqs=[] → 跳过分档节（合法）
- focus_freqs 非空且 sheet 存在 → 渲染
- focus_freqs 非空但 sheet 不存在 → exit 2（不跳过）

---

## 7. 报告渲染 + SKILL.md SOP 改动

### 7.1 compose_html.py 改动

新增一节"频点差值分档"，插在"差值曲线"和"一致性"之间：

- 只读 xlsx 渲染（不算数）
- focus_freqs 直接从 `params.json` 读（与 `run_freq_bins` 同源，不另传 CLI 参数，避免 PowerShell 编码问题）
- focus_freqs=[] → 整节跳过
- 每角度渲染 2 张表：明细 + 统计
- 表格用现有 CSS 类，统计表无左表头列
- L3 自检（见 §6.2）

### 7.2 SKILL.md SOP 改动

C 的 SKILL.md 改 4 处：

1. **intake 步骤**：加问"默认关注 1000Hz 差值，要不要加其他频点？"→ 写入 `params.focus_freqs`
2. **步骤3b 新增**：`run_freq_bins.py --params <产出目录>/params.json`
3. **步骤3c 编号顺移**：原步骤3b `run_consistency` → 步骤3c
4. **报告步骤**：加"频点差值分档"节说明

### 7.3 params.template.json 改动

加 `"focus_freqs": [1000]` 默认值。

### 7.4 references/ 改动

- `data-contract-sheets.md`：加 `freq_bins_<angle>` 和 `freq_bins_summary_<angle>` 两节
- `params.template.json`：加 `focus_freqs` 字段
- `report-outline.md`：加"频点差值分档"节大纲
- `fill-chat-summary.md`：加 intake 问 focus_freqs 的填法

---

## 8. 测试 + 错误处理

### 8.1 L1 单元测试（pytest，开发期）

`scripts/tests/test_run_freq_bins.py`：

- `test_basic_two_freqs`：2 频点 + 2 角度，验 sheet 数、列数、档位格式
- `test_none_delta`：含 None delta，验档位 = "N/A"
- `test_empty_focus_freqs`：`focus_freqs=[]`，验不写 sheet、exit 0
- `test_freq_out_of_band`：focus_freq 超分析频段，验跳过 + warning
- `test_idempotent`：跑两次，sheet 不重复
- `test_verification_fail_exit3`：mock 写入产生坏档位（如档位标签非法、列数错），验自检捕获 → exit 3 + sheet 被删
- `test_missing_delta_sheet_exit2`：缺 `delta_<angle>`，验 exit 2
- `test_invalid_focus_freqs_exit2`：focus_freqs 含负数/非数值/重复，验 exit 2
- `test_all_freqs_out_of_band_exit0`：所有 focus_freq 超频段，验 exit 0 + warning + 无 sheet

`scripts/tests/test_compose_freq_bins.py`（新增）：

- `test_render_freq_bins_section`：focus_freqs 非空 + sheet 存在，验 HTML 含节
- `test_skip_when_empty`：focus_freqs=[]，验 HTML 无节
- `test_exit2_when_sheet_missing`：focus_freqs 非空但 sheet 不存在，验 exit 2
- `test_report_verification_fail_exit3`：人为破坏 HTML，验 exit 3

### 8.2 L2/L3 集成测试（Playwright，可选）

**不在 SP1 必做范围**。SP1 只做 L1 + L2/L3 自检脚本本身。Playwright 端到端（params → xlsx → html → pdf → 解析 PDF 文本/表格）作为 SP1 验收后补强项，单独开任务。

### 8.3 错误处理总结

| 错误 | 退出码 | 处理 |
|------|-------|------|
| params.json 缺失/无 focus_freqs | exit 2 | 不跑，提示 Agent 补 params |
| focus_freqs 非法（负数/非数值/重复） | exit 2 | 不跑，提示 Agent 修 params |
| delta_<angle> sheet 缺失 | exit 2 | 不跑，提示 Agent 先跑 run_deltas |
| focus_freqs=[] | exit 0 | 合法跳过，不写 sheet |
| focus_freqs 非空但全部超频段 | exit 0 | warning，不写 sheet，不算失败 |
| focus_freq 超分析频段（部分） | warning + 跳过该频点 | 继续跑其他频点 |
| L2 自检失败 | exit 3 | 删坏 sheet，强制 askuser |
| L3 自检失败 | exit 3 | 不删 report.html，强制 askuser |
| compose_html: focus_freqs 非空但 sheet 不存在 | exit 2 | 强制 askuser（不能跳过） |

### 8.4 强制 askuser 的语义

- exit 2/3 → Agent 必须向用户报告 + 给出选项（修 params / 重跑 / 放弃该功能 / abort）
- Agent 不能"假装没事继续"——下游机械 gate 会拦
- 用户决策后 Agent 才能继续

---

## 9. 范围总结

### 9.1 SP1 改动清单

**新增文件**：
- `scripts/run_freq_bins.py`
- `scripts/tests/test_run_freq_bins.py`
- `scripts/tests/test_compose_freq_bins.py`

**改动文件**：
- `scripts/compose_html.py`（加节 + 读 params.json 取 focus_freqs + L3 自检）
- `SKILL.md`（intake 加问 + 步骤3b + 报告节）
- `references/params.template.json`（加 focus_freqs）
- `references/data-contract-sheets.md`（加两节）
- `references/report-outline.md`（加节大纲）
- `references/fill-chat-summary.md`（加 intake 填法）

**不动**：
- A、B、shared 任何文件
- C 的 `run_deltas.py` / `run_consistency.py` / `render_figures.py` / `quantize.py` / `angle_sheets.py` / `params_io.py` / `compose_pdf.py`
- C 的 `tests/test_run_deltas.py` / `tests/test_run_consistency.py` / `tests/test_angle_sheets.py` / `tests/test_compose_smoke.py`

### 9.2 验收标准

1. `focus_freqs=[1000]` 时，每角度产出 2 张 sheet（明细 + 统计），列数正确
2. `focus_freqs=[1000, 4000]` 时，列数 = 1 + 2×2（明细）/ 2×2（统计）
3. `focus_freqs=[]` 时，无 sheet、无报告节、exit 0
4. delta 含 None 时，档位 = "N/A"；统计表每频点求和 == 该频点非 None delta 数
5. 所有 present delta 同值时，bin 范围强制为 `[v, v+1)`，不出现空范围
6. focus_freqs 含非法值（负数/非数值/重复）→ exit 2
7. focus_freqs 非空但全部超分析频段 → exit 0 + warning + 无 sheet
8. focus_freq 部分超频段 → 跳过该频点 + warning，其余频点正常出列
9. L2 自检：mock 坏档位写入 → exit 3 + sheet 被删
10. L3 自检：人为破坏 HTML → exit 3
11. compose_html 在 focus_freqs 非空但 sheet 不存在时 exit 2
12. 所有 L1 测试通过

### 9.3 非目标重申

- ❌ 包络框、pass/fail 判定（已撤销）
- ❌ 走势分析、共振峰、分类（SP3）
- ❌ 改 A/B/shared
- ❌ 改 C 现有脚本
- ❌ 给现有脚本补机械验证（SP1 只给新脚本加）
- ❌ 解决 axial 被标准化两遍（已决定不改）
- ❌ Playwright 端到端（SP1 后补强）

### 9.4 后续

- SP1 实现完成 + 验收后 → 进入 writing-plans 出实现计划
- SP3（C 报告深化 + 走势分析）单独 brainstorm，不在 SP1 范围

---

## 10. 自审修订记录（2026-07-19）

初稿自审发现 7 处问题，已全部打入正文：

| 编号 | 位置 | 问题 | 修订 |
|------|------|------|------|
| A | §6.1 check 9 | 求和语义含糊（N/A 时求和 ≠ sample_count） | 改为"== 该频点非 None delta 数" |
| B | §5.3 | 所有 present delta 同值时 bin 范围为空 | 补边界规则：强制 `[v, v+1)` |
| C | §5.3 | `[f_lo, f_hi]` 来源未明 | 注明来自 params.json，与 run_deltas 同源 |
| D | §7.1 / §9.1 | `--focus-freqs-file` 与 params.json 关系未明 | 删除该参数，compose_html 直接读 params.json |
| E | §8.1 | `test_verification_fail_exit3` 描述错位 | 改为 mock 坏档位写入 |
| F | §5.2 / §8.1 / §8.3 | focus_freqs 输入校验缺失 | 补校验 gate（exit 2）+ 测试 + 错误表行 |
| G | §5.2 / §8.1 / §8.3 | 全部 focus_freq 超频段时退出码未定 | 定为 exit 0 + warning + 测试 + 错误表行 |

§9.2 验收标准同步从 8 条扩到 12 条，覆盖上述边界。
