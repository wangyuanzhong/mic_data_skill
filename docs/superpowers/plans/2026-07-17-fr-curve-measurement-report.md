# FR Curve Measurement Report Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 Cursor Skill `fr-curve-measurement-report`：含义合同引用、七类规定图（中文文件名）、四段正文版式、HTML→PDF 自适应组版，使 Agent 在选标产出目录上可复现出正式 PDF 报告。

**Architecture:** 选标产出的 `params.json` + `process.xlsx` 为唯一输入（不读 `process.md`）。报告 Skill 脚本只负责闸门检查、出图、组 HTML/PDF；Agent 按 `report-outline.md` 填四段大白话。含义字典放在选标 `references/data-contract.md`，报告侧只引用。

**Tech Stack:** Python 3.11+、pytest、openpyxl、matplotlib、Jinja2（或字符串模板）、Playwright（HTML→PDF）；Cursor Agent Skill（Markdown）。

**Spec:** `docs/superpowers/specs/2026-07-17-fr-curve-measurement-report-design.md`

## Global Constraints

- 输入仅 `params.json` + `process.xlsx`；禁止读 `process.md`；禁止探原始测量包；禁止重跑选标脚本；禁止手算数字。
- 闸门：`curve_meta.outlier_gate == confirmed`，且灵敏度/曲线结论 sheet 齐全。
- 横轴画满数据频段；分析框 / 包络框 / σ 计算频段用 `params.f_lo_hz`–`f_hi_hz`。
- 灵敏度只表不图。
- 插图顺序：奇异值图 → 剔异后叠图 → 包络分档_* → 金标 → 辅标偏差 → 辅标绝对 → 一致性 σ。
- 图文件名用中文（见 spec §5.1）；包络空壳不生成文件。
- 包络分档与选标同一 `max_abs→δ`（0.1 步进），出图按 0.5 dB 壳归堆。
- 一致性 σ 算法/样式对齐 bk-tool；频段用 params，不强制 20–20000。
- 改格式只改组版代码/CSS/模板。
- 样例原始测量不进仓库；测试用合成 xlsx/params。
- 提交用 conventional commits；**仅在用户明确要求时执行 `git commit`**（计划中的 Commit 步骤改为「列出待提交文件，等待用户下令」）。

---

## File Structure

```
.cursor/skills/fr-curve-golden-analysis/
└── references/
    └── data-contract.md          # params + 全 sheet 含义（生产者合同）

.cursor/skills/fr-curve-measurement-report/
├── SKILL.md                      # SOP
├── references/
│   └── report-outline.md         # 四段正文版式
└── scripts/
    ├── requirements.txt
    ├── xlsx_io.py                # 读宽表/meta/rank/decision
    ├── gates.py                  # 前置闸门
    ├── envelope_bins.py          # δ→0.5dB 壳分组
    ├── consistency.py            # σ(f) 计算
    ├── render_figures.py         # CLI：出全部图
    ├── plot_style.py             # 对数频轴、分析框、红包络
    ├── compose_html.py           # 扫描 figures + 填槽位 → report.html
    ├── compose_pdf.py            # HTML→PDF（Playwright）
    ├── templates/
    │   ├── report.html.j2
    │   └── report.css
    └── tests/
        ├── conftest.py           # 合成 process.xlsx + params.json fixture
        ├── test_gates.py
        ├── test_envelope_bins.py
        ├── test_consistency.py
        ├── test_render_figures.py
        └── test_compose.py
```

---

### Task 1: 选标侧 data-contract（含义目录）

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/references/data-contract.md`
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md`（交付物表加一行链接到 data-contract）

**Interfaces:**
- Consumes: 当前 `params.template.json` 与 `run_sensitivity.py` / `run_curves.py` 写出的 sheet 名与列名
- Produces: 人类可读合同；报告 Skill 通过相对路径引用

- [ ] **Step 1: 根据脚本列名起草 data-contract.md**

覆盖：
1. `params.json` 每个顶层/嵌套字段（含 `curves.exclude`：`null`=pending，`[]`/名单=confirmed）
2. 每个 sheet：用途、关键列、谁写（Agent 宽表 vs 哪支脚本）、报告是否常用

必列 sheet（与现脚本一致）：
`curves`, `sens_step1_pick1000`, `sens_step2_midline`, `sens_step3_bins`, `sensitivity`, `sensitivity_meta`, `curve_step1_level_ref`, `curve_step1_leveled`, `curve_mean_before_outlier`, `curve_step2_mean`, `outlier_review`, `outlier_decision`, `curve_mean_after_outlier`, `curve_step3_dev`, `curve_step3_dev_in_band`, `curve_step4_envelope`, `curve_rank`, `curve_meta`

- [ ] **Step 2: 在选标 SKILL.md 交付物表增加一行**

```markdown
| `references/data-contract.md` | params + process.xlsx 各 sheet 含义（报告 Skill 只引用） |
```

- [ ] **Step 3: 人工核对** — 打开 `run_sensitivity.py` / `run_curves.py` 的 `_replace_sheet` 与 `append` 表头，确认合同无漏列、无错名

- [ ] **Step 4: 待提交（等用户下令再 commit）**

```
git add .cursor/skills/fr-curve-golden-analysis/references/data-contract.md \
        .cursor/skills/fr-curve-golden-analysis/SKILL.md
# feat(analysis): add params/xlsx data-contract for report consumers
```

---

### Task 2: 合成 fixture + 闸门

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/requirements.txt`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/xlsx_io.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/gates.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/conftest.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_gates.py`

**Interfaces:**
- Produces:
  - `read_meta_kv(ws) -> dict[str, str]`
  - `read_wide_curves(ws) -> tuple[list[float], list[str], list[list[float|None]]]`
  - `check_report_ready(output_dir: Path) -> None`（失败 `SystemExit` 带中文原因）

- [ ] **Step 1: 写 requirements.txt**

```text
openpyxl>=3.1
matplotlib>=3.8
jinja2>=3.1
playwright>=1.40
pytest>=7.0
```

- [ ] **Step 2: 写失败测试 `test_gates.py`**

```python
from pathlib import Path
import pytest
from gates import check_report_ready

def test_missing_params_raises(tmp_path: Path):
    with pytest.raises(SystemExit, match="params.json"):
        check_report_ready(tmp_path)

def test_pending_outlier_gate_raises(synthetic_pending_dir: Path):
    with pytest.raises(SystemExit, match="outlier_gate"):
        check_report_ready(synthetic_pending_dir)

def test_confirmed_passes(synthetic_ready_dir: Path):
    check_report_ready(synthetic_ready_dir)  # no raise
```

- [ ] **Step 3: 跑测试确认失败**

Run: `cd .cursor/skills/fr-curve-measurement-report/scripts && python -m pytest tests/test_gates.py -v`  
Expected: FAIL（模块不存在或 fixture 未定义）

- [ ] **Step 4: 实现 conftest 合成 workbook**

`synthetic_ready_dir` 至少含：
- `params.json`：`product`, `note`, `unit`, `f_lo_hz=100`, `f_hi_hz=15000`, `sensitivity`, `curves.exclude=[]`, `output_dir` 指向自身
- `process.xlsx` sheets：`curves`, `curve_step1_leveled`, `curve_mean_before_outlier`, `curve_mean_after_outlier`, `curve_step3_dev`, `outlier_decision`, `curve_rank`, `curve_step4_envelope`, `curve_meta`（`outlier_gate=confirmed`, `golden`, `aux`）, `sensitivity`, `sensitivity_meta`

用 3～4 条合成样机、对数稀疏频点即可（如 100/1000/10000 Hz）。`synthetic_pending_dir` 同结构但 `outlier_gate=pending` 且无 rank 表。

- [ ] **Step 5: 实现 `xlsx_io.py` + `gates.py`**

`check_report_ready` 检查：
1. `params.json` / `process.xlsx` 存在  
2. 读取 `curve_meta` → `outlier_gate == confirmed`  
3. 必需 sheet 集合（与 spec §3.2 一致）均存在  

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest tests/test_gates.py -v`  
Expected: PASS

- [ ] **Step 7: 待提交（等用户下令）**

---

### Task 3: 包络 0.5 dB 分壳

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/envelope_bins.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_envelope_bins.py`

**Interfaces:**
- Consumes: `curve_rank` 行：`sample`, `delta`（或从 `max_abs_dev` 现算 δ）
- Produces: `bin_samples_by_envelope(rows: list[dict], step: float = 0.5) -> dict[float, list[str]]`  
  键为壳上沿 dB（0.5, 1.0, …）；值为该壳样机名；空壳不出现

规则（与 spec 一致）：
- δ 已是 0.1 步进最紧包络；壳 `k*0.5` 含 `( (k-1)*0.5 , k*0.5 ]`，且 k=1 时含 `δ≤0.5`

```python
import math

def envelope_shell(delta: float, step: float = 0.5) -> float:
    if delta <= 0:
        return step
    return math.ceil(delta / step - 1e-12) * step
```

- [ ] **Step 1: 写失败测试**

```python
from envelope_bins import bin_samples_by_envelope, envelope_shell

def test_shell_edges():
    assert envelope_shell(0.1) == 0.5
    assert envelope_shell(0.5) == 0.5
    assert envelope_shell(0.6) == 1.0
    assert envelope_shell(1.0) == 1.0

def test_bin_groups():
    rows = [
        {"sample": "A", "delta": 0.2},
        {"sample": "B", "delta": 0.5},
        {"sample": "C", "delta": 0.8},
    ]
    bins = bin_samples_by_envelope(rows)
    assert bins[0.5] == ["A", "B"]
    assert bins[1.0] == ["C"]
    assert 1.5 not in bins
```

- [ ] **Step 2: 跑测失败 → 实现 → 跑测通过**

- [ ] **Step 3: 待提交（等用户下令）**

---

### Task 4: 一致性 σ(f)

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/consistency.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_consistency.py`

**Interfaces:**
- Produces: `compute_sigma_curve(freqs, amps_by_sample: dict[str, list[float]], f_lo, f_hi) -> dict`  
  返回 `{"freqs_hz": [...], "sigma_db": [...], "f_lo": f_lo, "f_hi": f_hi}`  
  - 在**全freqs**上保留横轴点；对 `f_lo≤f≤f_hi` 的点算  
    `σ(f)=sample_std_i(A_i(f)-μ(f))`（样本标准差，ddof=1，与 bk-tool `_std_dev` 一致）  
  - 框外频点 `sigma_db` 置 `None`（出图时不画线/不填充）

参考：`E:/vibe/bk-tool (2)/bk-tool/bkcore/curve_consistency_core.py`（只移植 σ(f) 核心，不搬 UI）。

- [ ] **Step 1: 写失败测试**

```python
from consistency import compute_sigma_curve

def test_sigma_zero_when_identical():
    freqs = [100.0, 1000.0, 10000.0]
    amps = {"a": [0.0, 0.0, 0.0], "b": [0.0, 0.0, 0.0]}
    out = compute_sigma_curve(freqs, amps, 100.0, 15000.0)
    assert out["sigma_db"] == [0.0, 0.0, 0.0]

def test_sigma_none_outside_band():
    freqs = [50.0, 1000.0, 20000.0]
    amps = {"a": [0.0, 1.0, 0.0], "b": [0.0, -1.0, 0.0]}
    out = compute_sigma_curve(freqs, amps, 100.0, 15000.0)
    assert out["sigma_db"][0] is None
    assert out["sigma_db"][2] is None
    assert out["sigma_db"][1] > 0
```

- [ ] **Step 2: 跑测失败 → 实现 → 跑测通过**

- [ ] **Step 3: 待提交（等用户下令）**

---

### Task 5: 出图脚本（七类图）

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/plot_style.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/render_figures.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_render_figures.py`

**Interfaces:**
- Consumes: `check_report_ready`, `xlsx_io`, `envelope_bins`, `consistency`
- Produces: `render_all_figures(output_dir: Path, figures_dir: Path | None = None) -> list[Path]`  
  默认 `figures_dir = output_dir / "figures"`  
  CLI: `python render_figures.py --params <产出目录>/params.json`

**画图硬规则：**
- X：数据 min～max Hz，对数轴  
- 分析框：竖线或矩形标出 `f_lo`–`f_hi`（包络红线仅在框内画 ±shell 水平线，线宽加粗、红色）  
- 文件名（精确）：

| 产出 | 文件名 |
|------|--------|
| 逻辑3 | `奇异值与剔异前均值.png` |
| 逻辑2 | `剔异后归零叠图.png` |
| 逻辑1 | `包络分档_正负{shell:g}dB.png`（如 `正负0.5dB`） |
| 逻辑4 | `金标绝对与偏差.png` |
| 逻辑5 | `辅标偏差叠图.png` |
| 逻辑6 | `辅标绝对叠图.png` |
| 逻辑7 | `批量一致性sigma.png` |

插图逻辑顺序在 compose 任务处理；本任务只需保证文件落盘。无剔除样机时仍生成「奇异值」图（可仅 mean_before，并在标题注明无剔除）。无辅标时生成空辅标图或跳过：约定 **跳过且不报错**，compose 侧可缺图。

- [ ] **Step 1: 写失败测试（检查文件名集合）**

```python
from render_figures import render_all_figures

def test_render_creates_core_pngs(synthetic_ready_dir, tmp_path):
    fig_dir = tmp_path / "figures"
    paths = render_all_figures(synthetic_ready_dir, fig_dir)
    names = {p.name for p in paths}
    assert "奇异值与剔异前均值.png" in names
    assert "剔异后归零叠图.png" in names
    assert "金标绝对与偏差.png" in names
    assert "批量一致性sigma.png" in names
    assert any(n.startswith("包络分档_正负") and n.endswith(".png") for n in names)
```

- [ ] **Step 2: 跑测失败 → 实现 plot_style + render_figures → 跑测通过**

实现提示：
- 用 `matplotlib` Agg backend  
- 读 `outlier_decision`：`user_exclude=yes` → 奇异值曲线；`in_mean_after=yes` → 保留叠图  
- 金标/辅标：`curve_rank.role` 或 `curve_meta`  
- 逻辑4：双 y 或同一轴叠「绝对」与「偏差」——按 spec 同图两线；图例标明「金标绝对」「金标−均值」  
- σ 图：浅蓝填充 + 蓝线，对齐 bk-tool 观感即可（不必像素级复刻）

- [ ] **Step 3: 手工打开一张 PNG 目视**（对数轴、红包络、分析框）

- [ ] **Step 4: 待提交（等用户下令）**

---

### Task 6: HTML 组版（自适应多图）

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/templates/report.css`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/templates/report.html.j2`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/compose_html.py`
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_compose.py`

**Interfaces:**
- Produces: `compose_report_html(output_dir, *, intro_html, sensitivity_html, curves_notes_html, conclusion_html, figures_dir=None) -> Path`  
  写入 `output_dir/report.html`  
- `list_figures_in_report_order(figures_dir: Path) -> list[Path]`：固定序插入；`包络分档_*.png` 按 shell 数值升序插在「剔异后归零叠图」之后、「金标」之前

顺序算法：

```python
ORDER_FIXED = [
    "奇异值与剔异前均值.png",
    "剔异后归零叠图.png",
    # envelope bins injected here
    "金标绝对与偏差.png",
    "辅标偏差叠图.png",
    "辅标绝对叠图.png",
    "批量一致性sigma.png",
]
```

CSS 要求：
- `.figures { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }`  
- `img { max-width: 100%; height: auto; }`  
- `@media print`：避免标题后立刻分页（`break-after: avoid` on h2/h3）  
- 包络分档可独占一行或进同一 grid（默认进 grid，改格式时只改 CSS）

- [ ] **Step 1: 写失败测试**

```python
from compose_html import list_figures_in_report_order, compose_report_html

def test_figure_order_with_bins(tmp_path):
    d = tmp_path / "figures"
    d.mkdir()
    for name in [
        "批量一致性sigma.png",
        "包络分档_正负1.0dB.png",
        "奇异值与剔异前均值.png",
        "剔异后归零叠图.png",
        "包络分档_正负0.5dB.png",
        "金标绝对与偏差.png",
    ]:
        (d / name).write_bytes(b"")
    ordered = [p.name for p in list_figures_in_report_order(d)]
    assert ordered[0] == "奇异值与剔异前均值.png"
    assert ordered[1] == "剔异后归零叠图.png"
    assert ordered[2] == "包络分档_正负0.5dB.png"
    assert ordered[3] == "包络分档_正负1.0dB.png"
    assert ordered[4] == "金标绝对与偏差.png"

def test_compose_writes_html(synthetic_ready_dir, tmp_path):
    # presuppose figures exist from render or touch empty pngs
    ...
    html_path = compose_report_html(
        synthetic_ready_dir,
        intro_html="<p>介绍</p>",
        sensitivity_html="<table></table>",
        curves_notes_html="",
        conclusion_html="<p>结论</p>",
        figures_dir=tmp_path / "figures",
    )
    text = html_path.read_text(encoding="utf-8")
    assert "介绍" in text
    assert "奇异值与剔异前均值.png" in text or "奇异值" in text
```

- [ ] **Step 2: 实现模板 + compose_html → 测试通过**

模板四段槽位：`{{ intro_html }}`、`{{ sensitivity_html }}`、`{{ figure_blocks }}`、`{{ conclusion_html }}`；标题用产品名（从 params）。

- [ ] **Step 3: 待提交（等用户下令）**

---

### Task 7: PDF 渲染

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/compose_pdf.py`
- Modify: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_compose.py`（增加 PDF smoke，可用 pytest mark）

**Interfaces:**
- Produces: `html_to_pdf(html_path: Path, pdf_path: Path | None = None) -> Path`  
  CLI: `python compose_pdf.py --html <report.html> [--pdf <report.pdf>]`

实现：Playwright Chromium `page.pdf(format="A4", print_background=True)`。  
首次环境需 `playwright install chromium`（写入 scripts/README 或 SKILL 一步）。

- [ ] **Step 1: 写测试（有 chromium 则生成非空 PDF；否则 skip）**

```python
import pytest
from compose_pdf import html_to_pdf

@pytest.mark.integration
def test_pdf_smoke(tmp_path):
    html = tmp_path / "t.html"
    html.write_text("<html><body><h1>hi</h1></body></html>", encoding="utf-8")
    try:
        pdf = html_to_pdf(html)
    except Exception as e:
        pytest.skip(f"playwright unavailable: {e}")
    assert pdf.is_file() and pdf.stat().st_size > 100
```

- [ ] **Step 2: 实现 compose_pdf.py → 跑 integration 测**

- [ ] **Step 3: 待提交（等用户下令）**

---

### Task 8: Skill SOP + 正文版式 + stub 对齐

**Files:**
- Modify: `.cursor/skills/fr-curve-measurement-report/SKILL.md`（完整 SOP，替换「建设中」）
- Create: `.cursor/skills/fr-curve-measurement-report/references/report-outline.md`
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md` description/正文确认「不做正式报告」已存在（若缺则补一句指向报告 Skill）

**SKILL.md SOP（必须写清）：**

1. 确认产出目录；`check`/`render_figures` 前读 data-contract 链接  
2. `python .../render_figures.py --params <dir>/params.json`  
3. Agent 按 `report-outline.md` 从 sheet/params 组织四段 HTML 片段（大白话；灵敏度表；曲线节按插图序）  
4. `compose_html` → `compose_pdf`  
5. 聊天短结：PDF 路径 + 生成了哪些图（含包络分档张数）  
6. 用户要改格式 → 只改 `templates/report.css` / `compose_html.py` / 模板，重跑组版

**report-outline.md：** 四段标题、每段该抄哪些字段/sheet、语气（大白话、勿堆编程词）、插图顺序表。

- [ ] **Step 1: 写 report-outline.md**  
- [ ] **Step 2: 重写 SKILL.md（description 保持 Use when… 触发条件，勿在 description 里写流程摘要）**  
- [ ] **Step 3: 对照 spec 清单勾选一遍（输入、闸门、七图、四段、PDF、边界）**  
- [ ] **Step 4: 待提交（等用户下令）**

---

### Task 9: 端到端冒烟（合成目录）

**Files:**
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_e2e_smoke.py`

- [ ] **Step 1: 写 e2e：ready fixture → render_all_figures → compose_html →（可选）html_to_pdf**

```python
def test_e2e_figures_and_html(synthetic_ready_dir):
    from render_figures import render_all_figures
    from compose_html import compose_report_html
    figs = render_all_figures(synthetic_ready_dir)
    assert figs
    html = compose_report_html(
        synthetic_ready_dir,
        intro_html="<p>产品测试</p>",
        sensitivity_html="<p>灵敏度表</p>",
        curves_notes_html="",
        conclusion_html="<p>结论</p>",
    )
    assert html.is_file()
    assert "产品测试" in html.read_text(encoding="utf-8")
```

- [ ] **Step 2: 跑全量** `python -m pytest tests/ -v -m "not integration"`  
Expected: 全绿  

- [ ] **Step 3: 若本机已装 chromium，跑 integration PDF**  

- [ ] **Step 4: 待提交（等用户下令）**

---

## Spec coverage self-check

| Spec 项 | Task |
|---------|------|
| 不读 process.md；只吃 json+xlsx | 2, 8 |
| data-contract 在选标 references | 1 |
| 全部 sheet 可读 | 5（按需读） |
| 闸门 confirmed | 2 |
| 画满数据频段 + 框跟 json | 5 |
| 七类图 + 中文名 + 序 3214567 | 5, 6 |
| 包络 0.5 壳 + 红线 | 3, 5 |
| 一致性 σ ≈ bk-tool | 4, 5 |
| 灵敏度只表 | 8（outline） |
| 四段正文 | 8 |
| HTML→PDF + 可改组版 | 6, 7 |
| 与选标边界 | 8 |

## Placeholder scan

无 TBD/TODO；PDF 引擎已选定 Playwright；缺辅标时行为已约定为跳过文件。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-17-fr-curve-measurement-report.md`.

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每任务新开子代理，任务间复审  
2. **Inline Execution** — 本会话按 executing-plans 连续做，设检查点  

要走哪一种？
