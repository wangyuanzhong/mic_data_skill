# 数据合同：宽表 `curves`

本文件属报告 Skill `fr-curve-measurement-report`。  
选标 Agent 步骤2 写入；**改该 sheet 布局时，维护者须同步改本文**（见包 README）。

报告通常更常用 leveled 表（见 `data-contract-sheets-curves.md`）；本文件供对照原始绝对曲线底稿时使用。

## `curves`

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（纵轴）；A1 可为 `freq_hz` 或空 |
| 第 1 行 B 列起 | 样机名 |
| B2 起 | 该频率下该样机幅度（与 `params.json` 的 `unit` 一致） |
