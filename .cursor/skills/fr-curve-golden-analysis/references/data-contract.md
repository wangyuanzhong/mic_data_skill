# 选标产出数据合同（params.json + process.xlsx）

供报告 Skill `fr-curve-measurement-report` 与脚本消费者只读引用。  
**数字真源是 sheet；`params.json` 是元信息与传参；`process.md` 是过程日志，报告不读。**

---

## 1. params.json

| 字段 | 类型 | 含义 |
|------|------|------|
| `product` | string | 产品/型号名 |
| `note` | string | 说明；无则「无」 |
| `data_root` | string | 原始分析根目录路径 |
| `output_dir` | string | 本批产出目录（含本文件与 process.xlsx） |
| `unit` | string | 幅度单位（如 dBV、dB SPL） |
| `f_lo_hz` | number | 曲线分析频段下限 Hz（默认 100） |
| `f_hi_hz` | number | 曲线分析频段上限 Hz（默认 15000） |
| `process_xlsx` | string | 工作簿文件名，默认 `process.xlsx` |
| `process_md` | string | 过程日志文件名，默认 `process.md`（报告不读） |
| `sensitivity.midline_mode` | `"mean"` \| `"value"` | 灵敏度中线：整批平均 / 给定设计值 |
| `sensitivity.midline_db` | number \| null | `value` 时的中线数值；`mean` 时为 null |
| `curves.aux_count` | int | 曲线辅标个数（默认 3） |
| `curves.exclude` | null \| string[] | **null** = 奇异值门禁未确认（pending）；**[]** 或名单 = 已确认（confirmed） |
| `curves.q_threshold` | number | 高 Q 豁免阈值（默认 10） |

---

## 2. process.xlsx sheets

### 2.1 宽表（Agent 步骤2 写入）

#### `curves`

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（纵轴）；A1 可为 `freq_hz` 或空 |
| 第 1 行 B 列起 | 样机名 |
| B2 起 | 该频率下该样机幅度（与 `unit` 一致） |

报告：原始绝对曲线底稿；通常更常用 leveled 表。

---

### 2.2 灵敏度（`run_sensitivity.py`）

#### `sens_step1_pick1000`

列：`sample`, `target_hz`, `freq_used_hz`, `abs_freq_error_hz`, `level_at_freq_used`, `pick_note`, `unit`  
用途：每样机取最接近 1000 Hz 的点。

#### `sens_step2_midline`

上半 key/value：`midline_mode`, `midline_db`, `unit`, `n_samples`, `bin_width_db`  
下半表：`sample`, `level_1000`, `included_in_mean`, `contribution_note`

#### `sens_step3_bins`

列：`sample`, `freq_used_hz`, `level_1000`, `midline_db`, `delta_to_mid`, `abs_delta_to_mid`, `bin`, `bin_lo_db`, `bin_hi_db`, `pick_note`, `abs_delta_rank`, `role`, `unit`  
档宽 0.5 dB；`role=golden` 为灵敏度金标。

#### `sensitivity`（报告常用）

列：`sample`, `freq_used_hz`, `level_1000`, `delta_to_mid`, `bin`, `bin_lo_db`, `bin_hi_db`, `note`, `role`, `unit`  
结论表：写报告灵敏度节抄此表。

#### `sensitivity_meta`

key/value：`midline_mode`, `midline_db`, `unit`, `n_samples`, `bin_width_db`, `golden`, `golden_delta_to_mid`, `golden_bin`, `process_sheets`

---

### 2.3 曲线 / 奇异值（`run_curves.py`）

#### `curve_step1_level_ref`

列：`sample`, `target_hz`, `ref_freq_hz`, `abs_freq_error_hz`, `ref_level_db`, `level_formula`  
公式：`leveled = raw - ref_level_db`（约 1 kHz 归零）。

#### `curve_step1_leveled`（报告常用）

宽表：同 `curves` 布局，值为 1 kHz 归零后幅度。

#### `curve_mean_before_outlier` / `curve_step2_mean`

列：`freq_hz`, `mean_leveled_db`, `n_samples_at_freq`  
剔异前均值（全样机 leveled 平均）。`curve_step2_mean` 为兼容别名，内容同 before。

#### `outlier_review`

列：`sample`, `max_abs_dev_db`, `freq_at_max_hz`, `q_estimate`, `q_stable`, `exempt_high_q`, `exempt_reason`, `median_max_abs_db`, `threshold_db`, `suggest_exclude`, `suggest_reason`, `f_lo_hz`, `f_hi_hz`, `q_threshold`  
脚本提名；`suggest_exclude=yes` 为建议剔除。

#### `outlier_decision`（报告常用；仅 confirmed 后存在）

列：`sample`, `suggest_exclude`, `exempt_high_q`, `user_exclude`, `in_mean_after`, `decision_note`  
`user_exclude=yes` → 已剔除；`in_mean_after=yes` → 进入 mean_after / 排名。

#### `curve_mean_after_outlier`（报告常用）

同 mean 三列布局；剔异后保留样机的 leveled 均值。

#### `curve_step3_dev`

宽表：每样机相对 **mean_after** 的偏差（dB）；含已剔除样机（可追溯）。

#### `curve_step3_dev_in_band`

列：`freq_hz`, `in_analysis_band`, 各样机…  
框外偏差置空；`in_analysis_band` 为 yes/no。

#### `curve_step4_envelope`

列：`sample`, `max_abs_dev_db`, `freq_at_max_hz`, `delta_db`, `rms_db`, `n_points_in_band`, `f_lo_hz`, `f_hi_hz`, `delta_step_db`, `rank`, `role`, `excluded_from_mean`  
`delta_db` = 最紧包络（max_abs 按 0.1 dB 向上取整）；`role`：`golden` / `aux` / 空。

#### `curve_rank`（报告常用）

列：`sample`, `max_abs_dev`, `freq_at_max_abs`, `delta`, `rms`, `n_points_in_band`, `rank`, `role`  
曲线金标/辅标排名结论表。

#### `curve_meta`

key/value，常见键：
`aux_count`, `f_lo_hz`, `f_hi_hz`, `delta_step_db`, `n_samples_all`, `q_threshold`, `outlier_propose_min_dev_db`, `outlier_propose_median_factor`, `suggested_exclude`, `exempt_high_q`, **`outlier_gate`**（`pending` \| `confirmed`）, `excluded`, `n_samples_after_exclude`, `golden`, `aux`, `process_sheets`

报告闸门：**必须** `outlier_gate == confirmed`。

---

## 3. 报告消费者速查

| 需要 | 读哪里 |
|------|--------|
| 产品/频段/单位/说明 | `params.json` |
| 灵敏度表与金标 | `sensitivity`, `sensitivity_meta` |
| 归零绝对曲线 | `curve_step1_leveled` |
| 剔异前/后均值 | `curve_mean_before_outlier`, `curve_mean_after_outlier` |
| 谁被剔除 | `outlier_decision` |
| 偏差曲线 | `curve_step3_dev` |
| 金标/辅标/δ | `curve_rank` 或 `curve_meta` |
| 门禁是否可出报告 | `curve_meta.outlier_gate` |
