# FR Curve Directivity Analysis + shared Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地包级 `shared/`（公共 intake + 探查/确认 + 标准化约定）与独立 Skill `fr-curve-directivity-analysis`（一角度一 sheet → 对列求差 → 同角度一致性 → 本 Skill 内 HTML→PDF），且不破坏 A 选标业务脚本对单表 `curves` 的消费。

**Architecture:** `shared/` 无 `SKILL.md`、不参与 description 触发；A/C 的 SOP 引用其 fill/模板。A 标准化仍写出单表 `curves`（老脚本兼容）。C 标准化写出「一角度一 sheet」，脚本按列位对轴向求差。C 有独立产出目录与独立 `process.xlsx`。报告：脚本出图/组版；LLM 只传纯文本参数。包络合格标为后续可选任务（`envelope=null` 时跳过）。

**Tech Stack:** Python 3.11+、pytest、openpyxl、matplotlib、Jinja2、Playwright；Cursor Agent Skills（Markdown）。

**Spec:** `docs/superpowers/specs/2026-07-18-fr-curve-directivity-analysis-design.md`

## Global Constraints

- `shared/` **禁止**放 `SKILL.md`（不当可触发 Skill）。
- 角度相关 params/sheet **只增量**；不改名、不破坏 A 既有 sheet（`curves`、灵敏度/奇异值/金辅标相关）。
- A 业务脚本（`run_sensitivity.py` / `run_curves.py`）继续只读单表 `curves`；若 shared 抽离改变路径/导入，**同批改脚本并回归**现有 pytest。
- C 默认 `f_lo_hz=250`, `f_hi_hz=20000`；A 默认仍 `100`/`15000`。
- C 宽表：一角度一 sheet；列按序号；脚本对列求差；无 `curve_map`。
- 确认表格式写死：列头=角度，行=序号，单元格=文件名；确认前不写角度宽表、不跑计算。
- 正式报告不展示轴向曲线；数字不读 `process.md`。
- 报告尽量脚本；LLM 纯文本作 CLI/JSON 参数传入组版脚本。
- 提交用 conventional commits；**仅在用户明确要求时 `git commit`**（计划中 Commit 步骤改为「列出待提交文件，等用户下令」）。
- 样例原始测量不进仓库；测试用合成 xlsx/params。

### Plan 内锁死的默认（spec 未细写处；实现按此，勿再问）

| 项 | 默认 |
|----|------|
| A/C 产出 | **物理隔离**：各建自己的同级产出目录与 `process.xlsx` |
| Sheet 名安全 | 角度标签规范化为 `[A-Za-z0-9_]+`（如 `90°`→`90`）；`delta_<tag>` / `consistency_<tag>` |
| 一致性 v1 | 每个非轴向角度：逐频点跨样机 `std_db`；另写汇总行/表：`max_std_db`、`mean_std_db`、频段内 `max_minus_min_width_db`（样机间包络宽度在分析频段的最大值） |
| 包络合格 | **本 plan 不做**（Task 标可选）；`envelope` 恒可 `null`，不建 `pass_*` |
| C 报告图 v1 | 每非轴向角度一张「差值叠图」；一张「各角度一致性 σ」总图；无轴向图 |
| shared 与 A | 公共 fill/params 基础模板上抬 shared；A 的 SKILL 改相对链接；A 专有 fill（灵敏度/奇异值/曲线章）仍留 A |

---

## File Structure

```
.cursor/skills/
├── README.md                          # 更新：三 Skill + shared 边界
├── shared/                            # 无 SKILL.md
│   ├── README.md                      # 给人看：谁引用、禁止单独当 Skill
│   ├── references/
│   │   ├── params.base.template.json  # 公共字段（无 sensitivity/curves/envelope）
│   │   ├── fill-00-skeleton.md        # 公共骨架（章标题用占位，A/C 可追加）
│   │   ├── fill-01-explore.md         # 探查结论版式
│   │   └── fill-angle-file-table.md   # 角度×文件名确认表（C 必用；格式写死）
│   └── scripts/                       # 可选后续；本 plan 先不强制放标准化写表脚本
│       └── (空或 README 说明：宽表仍由 Agent 按约定写出)
│
├── fr-curve-golden-analysis/          # A：改链接到 shared；业务脚本不动合同
│   ├── SKILL.md
│   ├── references/
│   │   ├── params.template.json       # 基于 shared base + sensitivity/curves
│   │   ├── fill-00-skeleton.md        # 薄包装：链到 shared 或注明「见 shared + 下列 A 专有章」
│   │   └── fill-01/02/31/32/33/35…    # A 专有保留
│   └── scripts/                       # run_* 保持读 curves；仅改 import 路径若需要
│
└── fr-curve-directivity-analysis/     # C：新建
    ├── SKILL.md
    ├── references/
    │   ├── params.template.json       # base + angles/axial_angle/sample_count/envelope
    │   ├── fill-00-skeleton.md        # C 骨架（含差值/一致性/报告章）
    │   ├── fill-02-standardize.md     # 标准化核对日志
    │   ├── fill-chat-summary.md
    │   ├── report-outline.md          # 章节 + compose 参数说明
    │   └── data-contract-*.md         # C 侧合同（角度 sheet / delta / consistency）
    └── scripts/
        ├── requirements.txt
        ├── utf8_boot.py               # 可从 A/B 拷或薄包装
        ├── params_io.py
        ├── angle_sheets.py            # 读角度 sheet、校验列对齐、对列求差
        ├── run_deltas.py              # CLI：写 delta_<tag>
        ├── run_consistency.py         # CLI：写 consistency_<tag>
        ├── render_figures.py
        ├── compose_html.py
        ├── compose_pdf.py
        ├── templates/
        │   ├── report.html.j2
        │   └── report.css
        └── tests/
            ├── conftest.py
            ├── test_angle_sheets.py
            ├── test_run_deltas.py
            ├── test_run_consistency.py
            └── test_compose_smoke.py
```

---

### Task 1: 建立 `shared/` 骨架与公共 references

**Files:**
- Create: `.cursor/skills/shared/README.md`
- Create: `.cursor/skills/shared/references/params.base.template.json`
- Create: `.cursor/skills/shared/references/fill-00-skeleton.md`
- Create: `.cursor/skills/shared/references/fill-01-explore.md`
- Create: `.cursor/skills/shared/references/fill-angle-file-table.md`

**Interfaces:**
- Consumes: 现有 A 的 `fill-00-skeleton.md` / `fill-01-explore.md` / `params.template.json` 公共字段
- Produces: shared 公共模板；无 Python API

- [ ] **Step 1: 写 `shared/README.md`**

内容必须包含：
1. 本目录**不是** Skill（无 `SKILL.md`）
2. A/C 通过相对路径引用 `references/`
3. 整包安装；不要只拷单个 Skill

- [ ] **Step 2: 写 `params.base.template.json`**

```json
{
  "product": "",
  "note": "",
  "data_root": "",
  "output_dir": "",
  "unit": "",
  "f_lo_hz": null,
  "f_hi_hz": null,
  "process_xlsx": "process.xlsx",
  "process_md": "process.md"
}
```

说明：`f_lo_hz`/`f_hi_hz` 由各 Skill 模板覆盖默认，base 用 `null` 强制 Skill 侧填。

- [ ] **Step 3: 从 A 抽出公共骨架与探查 fill 到 shared**

- `fill-00-skeleton.md`：保留产出目录规则与公共 intake 字段；**不要**写死 A 的「灵敏度/奇异值/曲线」三章标题为唯一结构——改为「公共章 + 各 Skill 追加专有章」说明。
- `fill-01-explore.md`：从 A 现有版式迁入（探查结论 / 映射摘要表 / 预览）。

- [ ] **Step 4: 写死 `fill-angle-file-table.md`**

必须含示例表（与 spec §4 一致）：

```markdown
# 角度 × 文件名确认表（聊天展示；格式写死）

列头 = 角度（含轴向）；行 = 序号；单元格 = 文件名。

| 序号 | axis | 90 | 180 |
|------|------|----|-----|
| 1 | …_0.csv | …_90.csv | …_180.csv |
| 2 | … | … | … |

确认前禁止写出角度宽表、禁止跑差值脚本。
不自然处必须主动提出：缺格、错位、同序号文件名对不上、某角度样机数与轴向不一致、疑似映射反了、序号重复/不连续。
```

- [ ] **Step 5: 待提交（等用户下令）**

```
git add .cursor/skills/shared/
# feat(shared): add intake/explore/angle-table references
```

---

### Task 2: A 改为引用 shared（业务脚本合同不变）

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md`
- Modify: `.cursor/skills/fr-curve-golden-analysis/references/params.template.json`（注明基于 shared base）
- Modify: `.cursor/skills/fr-curve-golden-analysis/references/fill-00-skeleton.md`（链到 shared 或薄包装）
- Modify: `.cursor/skills/fr-curve-golden-analysis/references/fill-01-explore.md`（链到 shared）
- Test: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_outliers.py`
- Test: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_quantize.py`

**Interfaces:**
- Consumes: `../shared/references/*`
- Produces: A SOP 仍写出单表 `curves`；`run_sensitivity` / `run_curves` 行为不变

- [ ] **Step 1: 更新 A 的 fill-00 / fill-01**

在文件顶部加：

```markdown
公共版式真源：[`../../shared/references/fill-00-skeleton.md`](../../shared/references/fill-00-skeleton.md)
本文件仅保留 A 专有章标题（灵敏度 / 奇异值 / 曲线）与默认频段 100–15000。
```

（fill-01 同理链到 shared `fill-01-explore.md`；若内容完全相同可改为短文件只含链接 +「按 shared 填入 process.md」。）

- [ ] **Step 2: 更新 A `SKILL.md` 步骤0/1 的相对路径**

凡写 `references/fill-00-skeleton.md` / `fill-01-explore.md` 处，改为先读 shared，或读本 Skill 薄包装（薄包装再链 shared）。**步骤2 写 `curves` 单表的规则一字不改。**

- [ ] **Step 3: 回归 A 脚本测试**

Run:

```text
pytest .cursor/skills/fr-curve-golden-analysis/scripts/tests -v
```

Expected: PASS（与抽 shared 前相同）。若因 import 路径失败 → 同批修脚本，不得改 sheet 合同。

- [ ] **Step 4: 待提交（等用户下令）**

```
# refactor(analysis): point intake/explore fills at shared/
```

---

### Task 3: 脚手架 Skill C（SKILL.md + params + md 骨架）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/params.template.json`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/fill-00-skeleton.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/fill-02-standardize.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/fill-chat-summary.md`

**Interfaces:**
- Consumes: shared fill-00 / fill-01 / fill-angle-file-table；params.base
- Produces: C SOP 闸门串 `0→1/1b→2→3→4`

- [ ] **Step 1: 写 `params.template.json`**

```json
{
  "product": "",
  "note": "",
  "data_root": "",
  "output_dir": "",
  "unit": "",
  "f_lo_hz": 250,
  "f_hi_hz": 20000,
  "process_xlsx": "process.xlsx",
  "process_md": "process.md",
  "angles": [],
  "axial_angle": "",
  "sample_count": null,
  "envelope": null
}
```

- [ ] **Step 2: 写 C `fill-00-skeleton.md`**

公共 intake 同 shared；专有章至少：

```markdown
## 探查结论
## 角度×文件名确认
## 标准化与脚本入参
## 差值分析
## 一致性分析
## 报告
## 运行说明
```

默认频段写 **250–20000**。

- [ ] **Step 3: 写 C `SKILL.md`（完整 SOP）**

`description` 必须含触发词（directivity / 指向性 / 多角度频响）并排除金标选标与 B 选标报告。

SOP 对齐 spec §3：
0 Intake（shared 公共项 + 命名说明；默认频段不主动问）  
1 探查 → 1b 聊天贴确认表（shared `fill-angle-file-table.md`）→ 用户确认  
2 写 params 的 `angles`/`axial_angle`/`sample_count` → 一角度一 sheet → md 核对  
3 `run_deltas.py` → `run_consistency.py`（只 `--params`）  
4 出图 → 白话参数 → `compose_html` → `compose_pdf` → 短结  

铁律：确认前不写宽表；无 sheet 不手补；报告不画轴向；`envelope` 为 null 不跑合格。

- [ ] **Step 4: 待提交（等用户下令）**

```
# feat(directivity): scaffold skill SOP and params template
```

---

### Task 4: C 角度宽表读写与对列求差（库 + 测试）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/angle_sheets.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/utf8_boot.py`（从 A/B 拷贝同内容）
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/params_io.py`（可基于 A 的 `params_io.py` 精简）
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/conftest.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_angle_sheets.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/requirements.txt`

**Interfaces:**
- Consumes: `params.json` 中 `angles`, `axial_angle`, `sample_count`；xlsx 中与 `angles` 同名的 sheet
- Produces:
  - `normalize_angle_tag(label: str) -> str`
  - `read_angle_sheet(ws) -> tuple[list[float], list[str], list[list[float|None]]]`（freqs, sample_headers, columns）
  - `assert_columns_aligned(axial, other) -> None`（freqs 与列数一致，否则 raise）
  - `subtract_columns(a, b) -> list[list[float|None]]`（逐列逐点 a−b；任一侧 None → None）

- [ ] **Step 1: 写失败测试**

```python
# test_angle_sheets.py
from angle_sheets import normalize_angle_tag, subtract_columns, assert_columns_aligned

def test_normalize_angle_tag():
    assert normalize_angle_tag("90°") == "90"
    assert normalize_angle_tag("axis") == "axis"

def test_subtract_columns_aligned():
    a = [[1.0, 2.0], [3.0, 4.0]]
    b = [[0.5, 0.0], [1.0, 1.0]]
    out = subtract_columns(a, b)
    assert out == [[0.5, 2.0], [2.0, 3.0]]

def test_assert_columns_aligned_raises_on_width_mismatch():
    import pytest
    with pytest.raises(ValueError):
        assert_columns_aligned(
            freqs_a=[100.0], cols_a=[[1.0]],
            freqs_b=[100.0], cols_b=[[1.0], [2.0]],
        )
```

- [ ] **Step 2: Run 确认失败**

```text
pytest .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_angle_sheets.py -v
```

Expected: FAIL（模块不存在或函数未定义）

- [ ] **Step 3: 最小实现 `angle_sheets.py`**

实现上列四个 API。`normalize_angle_tag`：去空白、去 `°`/`deg` 后缀、非 `[A-Za-z0-9_]` 替换为 `_`、合并连续 `_`。

- [ ] **Step 4: Run 确认通过**

```text
pytest .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_angle_sheets.py -v
```

Expected: PASS

- [ ] **Step 5: 待提交（等用户下令）**

```
# feat(directivity): add angle sheet align and column subtract helpers
```

---

### Task 5: `run_deltas.py`（写 `delta_<tag>` sheet）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/run_deltas.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_deltas.py`
- Modify: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/conftest.py`（合成多角度 workbook fixture）

**Interfaces:**
- Consumes: `--params` → 读轴向 sheet + 各非轴向 sheet
- Produces: 每个非轴向角度一张 `delta_<normalize_angle_tag(angle)>`；列头与样机列顺序与源 sheet 一致；A 列频率

- [ ] **Step 1: 写 fixture + 失败测试**

`conftest.py` 合成：
- params：`axial_angle="axis"`, `angles=["axis","90"]`, `sample_count=2`
- sheets `axis` / `90`：同频率 2 点，各 2 列样机；90 比 axis 各大 1.0 dB

测试：跑 `run_deltas.main` 后 `delta_90` 全为 1.0。

- [ ] **Step 2: Run 确认失败 → 实现 `run_deltas.py` → Run 确认通过**

CLI：

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_deltas.py --params <out>/params.json
```

列数不一致 → `SystemExit` 非零，不写半成品 sheet。

- [ ] **Step 3: 脚本成功后可选 patch `process.md`「## 差值分析」**（仿 A 的 `patch_process_md_section`；无 md 则跳过不失败）

- [ ] **Step 4: 待提交（等用户下令）**

```
# feat(directivity): add run_deltas for per-angle column subtract
```

---

### Task 6: `run_consistency.py`（写 `consistency_<tag>`）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/run_consistency.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_consistency.py`

**Interfaces:**
- Consumes: 已有 `delta_<tag>` sheets；`params.f_lo_hz`/`f_hi_hz`
- Produces: 每非轴向角度一张 `consistency_<tag>`，至少列：
  - `freq_hz`, `std_db`, `max_db`, `min_db`, `width_db`（max−min）, `n_samples`, `in_analysis_band`（yes/no）
  - 另可一张 `consistency_summary`：`angle`, `max_std_db`, `mean_std_db`, `max_width_db`（仅分析频段内）

- [ ] **Step 1: 写失败测试（两样机差值恒等 → std≈0；再造发散样例 → width>0）**

- [ ] **Step 2: 实现 → pytest PASS**

CLI：

```text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_consistency.py --params <out>/params.json
```

依赖：先有 delta sheets；缺失则明确报错退出。

- [ ] **Step 3: 待提交（等用户下令）**

```
# feat(directivity): add run_consistency for same-angle dispersion
```

---

### Task 7: C 数据合同 + 标准化核对 fill

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/data-contract-params.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/data-contract-sheets.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/fill-02-standardize.md`
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md`（交付物表链到合同）

**Interfaces:**
- Produces: Agent/维护者可读合同；与脚本 sheet 名列一致

- [ ] **Step 1: 写 data-contract**

覆盖：C params 字段；角度宽表布局（同 A 的 curves 宽表习惯：A 列频率，第1行样机名）；`delta_*` / `consistency_*` / `consistency_summary`；明确 **不做** `pass_*`（本 plan）。

- [ ] **Step 2: 写 fill-02**（确认表已确认、各角度 sheet 行列数、序号对齐核对清单）

- [ ] **Step 3: 待提交（等用户下令）**

```
# docs(directivity): add data-contract and standardize fill
```

---

### Task 8: C 报告出图 + 组版（文本参数进脚本）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/render_figures.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/compose_html.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/compose_pdf.py`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/templates/report.html.j2`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/templates/report.css`
- Create: `.cursor/skills/fr-curve-directivity-analysis/references/report-outline.md`
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_smoke.py`
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md`（步骤4 命令与参数名）

**Interfaces:**
- Consumes: delta/consistency sheets；Agent CLI 文本参数
- Produces: `figures/*.png`, `report.html`, `report.pdf`

图文件名（写死）：
- `差值叠图_<tag>.png`（每个非轴向角度一张；叠多样机差值；**无轴向**）
- `一致性sigma.png`（可用多角度曲线或分面）

`compose_html.py` 参数（对齐 B 风格）：
- `--output-dir`
- `--intro-note`
- `--deltas-note`
- `--consistency-note`
- `--conclusion-note`

禁止 Agent 手写 `report.html` / 手建 `report_sections/`（若采用与 B 相同 note 落盘方式，只能由 compose 脚本写）。

- [ ] **Step 1: 写 `report-outline.md`**（章节顺序、传参说明、自检表、禁止展示轴向）

- [ ] **Step 2: 实现 `render_figures.py` + 合成数据冒烟**

```text
python .../render_figures.py --params <out>/params.json
```

Expected: `figures/` 非空且无文件名含「轴向」作为主曲线图。

- [ ] **Step 3: 实现 compose_html / compose_pdf**（可参考 B 的 Playwright 流程；模板独立在 C 下）

- [ ] **Step 4: `test_compose_smoke.py`** — 合成产出目录 → render → compose_html（白话可空）→ 断言 `report.html` 存在且含「差值」类标题

- [ ] **Step 5: 更新 C SKILL 步骤4 命令与铁律**

- [ ] **Step 6: 待提交（等用户下令）**

```
# feat(directivity): add figures and HTML/PDF compose pipeline
```

---

### Task 9: 包 README 与边界表

**Files:**
- Modify: `.cursor/skills/README.md`
- Modify: `docs/superpowers/specs/2026-07-17-mic-fr-skills-package-gap-analysis.md`（可选：勾掉 Skill C「未建」、注明 shared 已立）

**Interfaces:**
- Produces: 维护者可见的三 Skill + shared 流水线

- [ ] **Step 1: 重写包 README 表**

| Skill / 层 | 何时用 |
|------------|--------|
| `shared/` | 非触发；A/C 引用 |
| A 金标 | 选标 |
| B 选标报告 | 正式 PDF（选标产出） |
| C 指向性 | 多角度差值/一致性 + 本 Skill 内报告 |

删掉过时句「后续指向性……读取金标结果判新样」。

- [ ] **Step 2: 边界总表**（探原始 / 写 params / 写 xlsx / 出 PDF）按 spec §2.1 填写

- [ ] **Step 3: 待提交（等用户下令）**

```
# docs(skills): document shared + directivity in package README
```

---

### Task 10（可选，本 plan 可不做）: 包络合格 `pass_*`

仅当用户后续明确要求时开新 plan/task：定义 `envelope` 格式 → `run_pass.py` → 报告合格节。  
当前：`envelope: null`，不建 `pass_*`。

---

## Self-Review（对照 spec）

| Spec 要求 | 对应 Task |
|-----------|-----------|
| shared 抬高 intake/探查/确认版式 | Task 1 |
| A 引用 shared；curves 合同与老脚本兼容 | Task 2 |
| C Skill + 默认 250–20000 + 闸门 | Task 3 |
| 一角度一 sheet；对列求差；无 curve_map | Task 4–5 |
| 同角度一致性 | Task 6 |
| 完整 xlsx + process.md 日志 | Task 3/5/6/7 |
| C 内 HTML→PDF；LLM 文本参数；不画轴向 | Task 8 |
| 包 README | Task 9 |
| 包络合格 | Task 10 可选（spec §8.5） |
| 动 sheet 必改老脚本并回归 | Task 2 Step 3 |

Placeholder scan: 无 TBD 步骤；开放点已在 Global Constraints「Plan 内锁死的默认」表写死。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-18-fr-curve-directivity-analysis.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每 Task 派一个新 subagent，Task 间审查，迭代快  
2. **Inline Execution** — 本会话用 executing-plans 按 Task 推进，设检查点  

Which approach?
