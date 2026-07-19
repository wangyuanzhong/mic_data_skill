# 指向性分析报告版式

本文件属指向性 Skill `fr-curve-directivity-analysis`。Agent 在步骤4 准备白话参数与自检时按需读。

## 章节顺序（固定）

1. **整体介绍**：脚本从 `params.json` 生成介绍字段表；Agent 可加一段 `--intro-note` 白话。
2. **差值分析**：脚本插入 `figures/差值叠图_<tag>.png`（每非轴向角度一张）；Agent 可加 `--deltas-note`。
3. **频点差值分档**：脚本从 `freq_bins_<tag>` / `freq_bins_summary_<tag>` sheet 渲染明细表 + 统计表（每非轴向角度各两张）；`focus_freqs=[]` 时整节跳过。Agent 无需手写该节。
4. **一致性分析**：脚本从 `consistency_summary` sheet 生成汇总表 + 插入 `figures/一致性sigma.png`；Agent 可加 `--consistency-note`。
5. **结论**：Agent 写 `--conclusion-note`。

## 传参（对应 compose_html.py 参数）

| 参数 | 写什么 | 数字从哪 |
|------|--------|----------|
| `--intro-note` | 批次/产品介绍一两句 | `params.json`（脚本自动列表） |
| `--deltas-note` | 差值形态说明（哪个角度偏离大、频段特征） | `delta_*` sheet（Agent 看，不抄整表） |
| `--consistency-note` | 一致性观察（哪个角度散度大） | `consistency_*` / `consistency_summary` |
| `--conclusion-note` | 结论三四句 | 同上 |

要求：纯白话；不要表；不要尖括号标签（PowerShell 会把 `<>` 当重定向）。

## 脚本生成（Agent 勿重复）

- 介绍字段表：由 `compose_html.py` 从 `params.json` 生成
- 一致性汇总表：由 `compose_html.py` 从 `consistency_summary` sheet 生成
- 图：由 `render_figures.py` 生成到 `figures/`
- `report.html` / `report_sections/`：由 `compose_html.py` 写

**禁止** Agent 手写 `report.html`、手建 `report_sections/`、手写介绍字段表或一致性汇总表。

## 不展示轴向曲线

报告**不画**轴向频响曲线。轴向 sheet 保留在 xlsx 供计算用，但不出现在报告图里。

## envelope=null 时的合格结论

`envelope` 为 `null`（本 plan 默认）时，报告**不得**写「合格 / 不合格 / 通过 / 失败」一类判定语。只描述差值与一致性。

## 自检（组版后、短结前；打开 `<out>/report.html` 用搜索核对）

| 项 | 通过条件 |
|----|----------|
| A. 介绍字段表 | 含「产品」「分析频段」「角度列表」「轴向参考」「样机数」行 |
| B. 差值叠图 | 每个非轴向角度一张；文件名 `差值叠图_<tag>.png`；图标题含角度名 |
| C. 一致性汇总表 | 含 `angle` / `max_std_db` / `mean_std_db` / `max_width_db` 列 |
| D. 一致性 σ 图 | `一致性sigma.png` 已插入 |
| E. 无轴向曲线 | 报告内无「轴向频响」「轴向曲线」一类图或独立轴向章节 |
| F. 无合格判定（envelope=null 时） | 报告正文不出现「合格 / 不合格 / 通过 / 失败」 |
| G. 四段 note | `report_sections/` 下四个 txt 存在（可为空文件） |
| H. 频点差值分档节 | `focus_freqs` 非空时含"频点差值分档"节标题 + 每角度明细表 + 统计表 |
| I. 频点节列数 | 明细表列数 == 1 + 2×len(focus_freqs)；统计表列数 == 2×len(focus_freqs) |
