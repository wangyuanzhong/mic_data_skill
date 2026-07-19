# LLM 硬约束：分类微调与峰谷勾选（C 指向性）

本文件属指向性 Skill `fr-curve-directivity-analysis`。步骤 3.5 / 3.7 由 Agent/LLM 回写 xlsx 时**必须**遵守。

## 铁律

1. 一切数值（距离、k、类均值、峰谷频率/幅度/Q/prominence）只由脚本写 xlsx；LLM **不算数、不改数**。
2. LLM 只允许改两处：`cluster_final_<tag>` 的 `cluster_id` / `cluster_name`；`peak_candidates_<tag>` 的 `selected`。
3. 报告与出图只读 `cluster_final` + `peak_candidates` 中 `selected=yes`。

## 分类微调（步骤 3.5）

**可改：** 仅 `cluster_final_<tag>`。

**禁止改：** `cluster_dist_<tag>`、`cluster_suggest_<tag>`、`cluster_meta_<tag>` 中任何数值或结构。

**允许操作：**

- 为各类命名（`cluster_name`）
- 合并类（把样机改到同一 `cluster_id`）
- 把明显离群样机单独成类

**不强制 askuser**；分错可重跑 cluster/peaks。

**矛盾改动：** 若把某样机改到与距离矩阵最近邻多数类**严重矛盾**的类，必须在 `process.md` 写明理由（日志用途，非数字真源）。

## 峰谷勾选（步骤 3.7）

**可改：** 仅 `peak_candidates_<tag>.selected`（`yes` / `no`）。

**禁止改：** `cluster_id`、`kind`、`freq_hz`、`amplitude_db`、`q`、`prominence_db`。

**勾选原则：**

- 只勾「肉眼明显」的峰/谷
- 小起伏、噪声起伏保持 `no`
- 报告与 `render_trend_figures.py` 只展示 `selected=yes`

## 失败处理

脚本 exit 2（前置缺失/非法 params）或 exit 3（L2/L3 自检失败）→ 向用户说明并询问是否重跑/改 params；**禁止静默跳过**。
