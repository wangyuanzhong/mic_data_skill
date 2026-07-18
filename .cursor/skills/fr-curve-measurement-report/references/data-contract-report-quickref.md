# 数据合同：报告消费者速查

本文件属报告 Skill `fr-curve-measurement-report`。  
报告闸门与「读哪里」总表；字段细节见同目录其它 `data-contract-*.md`。

| 需要 | 读哪里 | 含义文件（按需打开） |
|------|--------|----------------------|
| 产品/频段/单位/说明 | `params.json` | [`data-contract-params.md`](data-contract-params.md) |
| 灵敏度表与金标 | `sensitivity`, `sensitivity_meta` | [`data-contract-sheets-sensitivity.md`](data-contract-sheets-sensitivity.md) |
| 原始绝对曲线宽表 | `curves` | [`data-contract-sheets-curves-wide.md`](data-contract-sheets-curves-wide.md) |
| 归零绝对曲线 | `curve_step1_leveled` | [`data-contract-sheets-curves.md`](data-contract-sheets-curves.md) |
| 剔异前/后均值 | `curve_mean_before_outlier`, `curve_mean_after_outlier` | 同上 |
| 谁被剔除 | `outlier_decision` | 同上 |
| 偏差曲线 | `curve_step3_dev` | 同上 |
| 金标/辅标/δ | `curve_rank` 或 `curve_meta` | [`data-contract-sheets-curves.md`](data-contract-sheets-curves.md)、[`data-contract-curve-meta.md`](data-contract-curve-meta.md) |
| 门禁是否可出报告 | `curve_meta.outlier_gate` | [`data-contract-curve-meta.md`](data-contract-curve-meta.md) |
