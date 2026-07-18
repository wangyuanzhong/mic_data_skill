# 数据合同：灵敏度 sheets

本文件属报告 Skill `fr-curve-measurement-report`。  
由选标 `run_sensitivity.py` 写入；**改灵敏度 sheet/列时，维护者须同步改本文**（见包 README）。

## `sens_step1_pick1000`

列：`sample`, `target_hz`, `freq_used_hz`, `abs_freq_error_hz`, `level_at_freq_used`, `pick_note`, `unit`  
用途：每样机取最接近 1000 Hz 的点。

## `sens_step2_midline`

上半 key/value：`midline_mode`, `midline_db`, `unit`, `n_samples`, `bin_width_db`  
下半表：`sample`, `level_1000`, `included_in_mean`, `contribution_note`

## `sens_step3_bins`

列：`sample`, `freq_used_hz`, `level_1000`, `midline_db`, `delta_to_mid`, `abs_delta_to_mid`, `bin`, `bin_lo_db`, `bin_hi_db`, `pick_note`, `abs_delta_rank`, `role`, `unit`  
档宽 0.5 dB；`role=golden` 为灵敏度金标。

## `sensitivity`（报告常用）

列：`sample`, `freq_used_hz`, `level_1000`, `delta_to_mid`, `bin`, `bin_lo_db`, `bin_hi_db`, `note`, `role`, `unit`  
结论表：写报告灵敏度节抄此表。

## `sensitivity_meta`

key/value：`midline_mode`, `midline_db`, `unit`, `n_samples`, `bin_width_db`, `golden`, `golden_delta_to_mid`, `golden_bin`, `process_sheets`
