# 数据合同：process.xlsx sheets（C 指向性）

本文件属指向性 Skill `fr-curve-directivity-analysis``。  
由 Agent（步骤2 角度宽表）与脚本（步骤3 `delta_*` / `freq_bins_*` / `consistency_*`）写入；报告脚本只读。  
**改 sheet/列时维护者须同步改本文与脚本。**

## 角度宽表（步骤2，Agent 写）

每个角度一张 sheet，sheet 名 = `normalize_angle_tag(angle)`（如 `axis` / `90` / `180`；`90°`→`90`）。

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（纵轴，自上而下）；A1 可为 `freq_hz` 或空 |
| 第 1 行 B 列起 | 样机名（按序号顺序） |
| B2 起 | 该频率下该样机的幅度 dB |

各角度 sheet **同序号同列位**；频率列（A 列）一致。  
轴向 sheet 名 = `normalize_angle_tag(params.axial_angle)`。

## `delta_<tag>`（步骤3，`run_deltas.py` 写）

每个非轴向角度一张。布局同角度宽表（A 列频率，第1行样机名，B2 起差值）。  
值 = 该角度 sheet − 轴向 sheet，按列位逐点求差；任一侧空 → 空。  
轴向角度不生成 `delta_*`。

## `freq_bins_<tag>`（步骤3，`run_freq_bins.py` 写）

每个非轴向角度一张。明细表：每行一个样机，列 = 样机 + 每个关注频点 ×（差值, 档位）。

| 位置 | 内容 |
|------|------|
| A 列 | 样机名 |
| 第 1 行 B 列起 | 交替列头：`<freq>Hz差值` / `<freq>Hz档位` |
| B2 起 | 该样机在该频点的差值（float 或空）与档位（`"lo~hi"` 1dB 左闭右开，或 `N/A`） |

档位规则：`floor(d)~floor(d)+1`；差值为 None → 档位 `N/A`。
`focus_freqs=[]` 时不生成任何 `freq_bins_*` sheet。

## `freq_bins_summary_<tag>`（步骤3，`run_freq_bins.py` 写）

每个非轴向角度一张。统计表，**无左表头**（A1 = 第一个频点的"分组"标题）。

| 位置 | 内容 |
|------|------|
| 第 1 行 | 交替列头：`<freq>分组` / `<freq>每组数量` |
| A2 起 | 该频点各 bin 的下界标签 `"lo~hi"` |
| B2 起 | 该 bin 的样机计数 |

各频点独立分档（`floor(min) ~ ceil(max)` 跨样机）；bin 数不同时短列下方留空。
每频点"每组数量"列求和 == 该频点非 None delta 数。

## `consistency_<tag>`（步骤3，`run_consistency.py` 写）

每个非轴向角度一张。列：

| 列 | 含义 |
|----|------|
| `freq_hz` | 频率 |
| `std_db` | 该频点跨样机差值的总体标准差（pstdev） |
| `max_db` | 该频点跨样机差值最大 |
| `min_db` | 该频点跨样机差值最小 |
| `width_db` | `max_db − min_db` |
| `n_samples` | 该频点非空样机数 |
| `in_analysis_band` | `yes`/`no`，按 `params.f_lo_hz..f_hi_hz` |

## `consistency_summary`（步骤3，`run_consistency.py` 写）

| 列 | 含义 |
|----|------|
| `angle` | 角度标签（原值，未规范化） |
| `max_std_db` | 分析频段内各频点 `std_db` 的最大 |
| `mean_std_db` | 分析频段内各频点 `std_db` 的均值 |
| `max_width_db` | 分析频段内各频点 `width_db` 的最大 |

## 不在本 plan 的 sheet

- `pass_<tag>`：仅当 `envelope` 非空时由后续 `run_pass.py` 写；**本 plan 不建**。
- 轴向曲线图：xlsx 保留轴向 sheet，但**报告不画轴向曲线**。
