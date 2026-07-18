# 数据合同：曲线 / 奇异值 sheets（不含 curve_meta）

本文件属报告 Skill `fr-curve-measurement-report`。  
由选标 `run_curves.py` 写入；**改这些 sheet/列时，维护者须同步改本文**（见包 README）。

闸门与 `outlier_gate` 见单独文件 [`data-contract-curve-meta.md`](data-contract-curve-meta.md)。

## `curve_step1_level_ref`

列：`sample`, `target_hz`, `ref_freq_hz`, `abs_freq_error_hz`, `ref_level_db`, `level_formula`  
公式：`leveled = raw - ref_level_db`（约 1 kHz 归零）。

## `curve_step1_leveled`（报告常用）

宽表：同 `curves` 布局（见 [`data-contract-sheets-curves-wide.md`](data-contract-sheets-curves-wide.md)），值为 1 kHz 归零后幅度。

## `curve_mean_before_outlier` / `curve_step2_mean`

列：`freq_hz`, `mean_leveled_db`, `n_samples_at_freq`  
剔异前均值（全样机 leveled 平均）。`curve_step2_mean` 为兼容别名，内容同 before。

## `outlier_review`

列：`sample`, `max_abs_dev_db`, `freq_at_max_hz`, `q_estimate`, `q_stable`, `exempt_high_q`, `exempt_reason`, `median_max_abs_db`, `threshold_db`, `suggest_exclude`, `suggest_reason`, `f_lo_hz`, `f_hi_hz`, `q_threshold`  
脚本提名；`suggest_exclude=yes` 为建议剔除。

## `outlier_decision`（报告常用；仅 confirmed 后存在）

列：`sample`, `suggest_exclude`, `exempt_high_q`, `user_exclude`, `in_mean_after`, `decision_note`  
`user_exclude=yes` → 已剔除；`in_mean_after=yes` → 进入 mean_after / 排名。

## `curve_mean_after_outlier`（报告常用）

同 mean 三列布局；剔异后保留样机的 leveled 均值。

## `curve_step3_dev`

宽表：每样机相对 **mean_after** 的偏差（dB）；含已剔除样机（可追溯）。

## `curve_step3_dev_in_band`

列：`freq_hz`, `in_analysis_band`, 各样机…  
框外偏差置空；`in_analysis_band` 为 yes/no。

## `curve_step4_envelope`

列：`sample`, `max_abs_dev_db`, `freq_at_max_hz`, `delta_db`, `rms_db`, `n_points_in_band`, `f_lo_hz`, `f_hi_hz`, `delta_step_db`, `rank`, `role`, `excluded_from_mean`  
`delta_db` = 最紧包络（max_abs 按 0.1 dB 向上取整）；`role`：`golden` / `aux` / 空。

## `curve_rank`（报告常用）

列：`sample`, `max_abs_dev`, `freq_at_max_abs`, `delta`, `rms`, `n_points_in_band`, `rank`, `role`  
曲线金标/辅标排名结论表。
