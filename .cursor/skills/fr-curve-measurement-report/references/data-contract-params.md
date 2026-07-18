# 数据合同：params.json

本文件属报告 Skill `fr-curve-measurement-report`。  
选标脚本写出这些字段；**改 params 字段时，维护者须同步改本文**（见包 README）。

**数字真源是 process.xlsx sheet；`params.json` 是元信息与传参；`process.md` 是过程日志，报告不读。**

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
