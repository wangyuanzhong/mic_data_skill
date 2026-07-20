# 数据合同：params.json（C 指向性）

本文件属指向性 Skill `fr-curve-directivity-analysis`。  
由 Agent 在步骤0/2 写入 `params.json`；脚本（`run_deltas` / `run_consistency` / `render_figures` / `compose_html`）只读这个。  
**改字段时维护者须同步改本文与脚本。**

公共字段（与 A 共用，定义见 [`../../shared/references/params.base.template.json`](../../shared/references/params.base.template.json)）：`product` / `note` / `data_root` / `output_dir` / `unit` / `f_lo_hz` / `f_hi_hz` / `process_xlsx` / `process_md`。

## C 专有字段

| 字段 | 类型 | 含义 | 谁写 | 何时 |
|------|------|------|------|------|
| `f_lo_hz` | number | 曲线分析频段下限 Hz；C 默认 **250** | Agent 步骤0 | intake |
| `f_hi_hz` | number | 曲线分析频段上限 Hz；C 默认 **20000** | Agent 步骤0 | intake |
| `angles` | string[] | 有序角度标签列表（含轴向）；顺序以确认表列头为准 | Agent 步骤2 | 确认后 |
| `axial_angle` | string | 轴向参考角度标签（必须 ∈ `angles`） | Agent 步骤2 | 确认后 |
| `sample_count` | number | 序号个数（各角度 sheet 列数） | Agent 步骤2 | 确认后 |
| `focus_freqs` | number[] | 关注频点 Hz；默认 `[1000]` | Agent 步骤0 | intake |
| `cluster_k_max` | number | 聚类 k 上限 | 模板默认 | — |
| `peak_prominence_db` | number | 峰谷 prominence 门槛 | 模板默认 | — |
| `peak_min_octave` | number | 峰谷最小八度间距 | 模板默认 | — |
| `peak_include_q` | boolean | 是否输出 Q | 模板默认 | — |

## 与 A 的区别

- A 有 `sensitivity.*` / `curves.aux_count` / `curves.exclude`；C **不写**。
- C 有 `angles` / `axial_angle` / `sample_count` / `focus_freqs` 等；A **不写**。
- 默认频段不同：A `100/15000`；C `250/20000`。
