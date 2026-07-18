# 数据合同：`curve_meta`（含报告闸门）

本文件属报告 Skill `fr-curve-measurement-report`。  
由选标 `run_curves.py` 写入；**改 `curve_meta` 键名时，维护者须同步改本文**（见包 README）。

其它曲线 sheet 见 [`data-contract-sheets-curves.md`](data-contract-sheets-curves.md)。

## `curve_meta`

key/value，常见键：
`aux_count`, `f_lo_hz`, `f_hi_hz`, `delta_step_db`, `n_samples_all`, `q_threshold`, `outlier_propose_min_dev_db`, `outlier_propose_median_factor`, `suggested_exclude`, `exempt_high_q`, **`outlier_gate`**（`pending` \| `confirmed`）, `excluded`, `n_samples_after_exclude`, `golden`, `aux`, `process_sheets`

报告闸门：**必须** `outlier_gate == confirmed`。
