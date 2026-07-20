# 数据合同：process.xlsx sheets（C 指向性）

本文件属指向性 Skill `fr-curve-directivity-analysis`。
由 Agent（步骤2 角度宽表）与脚本（步骤3 `delta_*` / `freq_bins_*` / `consistency_*` / `cluster_*` / `class_mean_*` / `peak_candidates_*`）写入；Agent/LLM 可微调 `cluster_final` 与 `peak_candidates.selected`（见 [`cluster-llm-rules.md`](cluster-llm-rules.md)）。报告脚本只读。  
**改 sheet/列时维护者须同步改本文与脚本。**

## 角度宽表（步骤2，Agent 写）

每个角度一张 sheet，sheet 名 = `normalize_angle_tag(angle)` / `angle_sheet_name(angle)`（如 `axis` / `90` / `180`；`90°`→`90`）。  
`params.angles` / `axial_angle` 可保留带 `°` 的显示标签；**脚本读宽表时一律用规范化名查找**（`run_deltas.py` 等），不要用 params 原文当 sheet 名。

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

## `cluster_dist_<tag>`（步骤3，`run_cluster.py` 写）

每个非轴向角度一张。样机×样机欧氏距离矩阵（raw delta，不中心化）。

| 位置 | 内容 |
|------|------|
| 第 1 行 B 列起 | 样机名（列头，与 `delta_<tag>` 列序一致） |
| A 列第 2 行起 | 样机名（行头） |
| B2 起 | 两机间欧氏距离；对角为 0；矩阵对称 |

有效频点数为 0 的样机不进矩阵核心（或相关格为空并 warning）。

## `cluster_suggest_<tag>`（步骤3，`run_cluster.py` 写）

每个非轴向角度一张。脚本建议分类。

| 列 | 含义 |
|----|------|
| `sample` | 样机名 |
| `cluster_id` | 建议类 id（从 1 起）；无法参与则为 `unclustered` |
| `dist_to_center` | 到类中心（类内均值向量）的欧氏距离；`unclustered` 为空 |

## `cluster_meta_<tag>`（步骤3，`run_cluster.py` 写）

每个非轴向角度一张。轮廓系数选 k 的元信息。

| 列 | 含义 |
|----|------|
| `k` | 候选类数 |
| `silhouette` | 该 k 的平均轮廓系数；`k=1` 时为字符串 `N/A`（不参与 argmax） |
| `chosen` | `yes`/`no`：是否为最终选中的 k |

另在 sheet 顶部或首行备注区写 `chosen_k`（与 `chosen=yes` 那一行一致）。

## `cluster_final_<tag>`（步骤3，Agent/LLM 写；脚本仅在「不存在」时从 suggest 复制）

每个非轴向角度一张。最终分类（报告与出图真源）。

| 列 | 含义 |
|----|------|
| `sample` | 样机名 |
| `cluster_id` | 最终类 id |
| `cluster_name` | 类名（可空；空则报告显示「类{id}」） |

**重跑 `run_cluster`：若 final 已存在则不覆盖。**

## `class_mean_<tag>`（步骤3，`run_peaks.py` 写）

每个非轴向角度一张。各类 delta 均值曲线。

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（与 delta 对齐，分析频段内） |
| 第 1 行 B 列起 | 类列名：`类{id}` 或 final 中的 `cluster_name`（同 id 取首次非空名） |
| B2 起 | 该类样机在该频点的 delta 均值（类内该频点全 None → 空） |

## `peak_candidates_<tag>`（步骤3，`run_peaks.py` 写）

每个非轴向角度一张。类均值峰谷候选；LLM 只改 `selected`。

| 列 | 含义 |
|----|------|
| `cluster_id` | 类 |
| `kind` | `peak` / `valley` |
| `freq_hz` | 中心频率 |
| `amplitude_db` | 类均值曲线在该点的幅度 |
| `q` | 品质因数；无法算则为 `N/A` |
| `prominence_db` | 突出度 |
| `selected` | `yes` / `no`（脚本初值全 `no`；LLM 只改此列） |

重跑 peaks：按 `(cluster_id, kind, freq_hz)` 匹配旧行以保留 `selected=yes`。匹配规则：在新候选中找满足 `|f_new - f_old| / f_old ≤ 0.005`（0.5%）的最近一条；多条命中取 |Δf| 最小；无命中则该旧勾选丢弃，新候选保持 `no`。

报告与出图**只使用** `selected=yes` 的行。

## 不在本 plan 的 sheet

- `pass_<tag>`：仅当 `envelope` 非空时由后续 `run_pass.py` 写；**本 plan 不建**。
- 轴向曲线图：xlsx 保留轴向 sheet，但**报告不画轴向曲线**。
