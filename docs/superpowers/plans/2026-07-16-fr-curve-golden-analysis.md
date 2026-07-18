# FR Curve Golden Analysis Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本仓库落地 Cursor Skill `fr-curve-golden-analysis`：SOP + 布局参考 + 报告模板 + 可重复计算脚本（双轨标准、过程工作簿、规定图），使 Agent 按设计文档跑通「探查→门禁→算→报告」。

**Architecture:** Skill（`SKILL.md` + templates/references）约束 Agent 流程与门禁；Python 包 `fr_analysis` 只吃「映射+参数+原文件路径」，输出每产品一份 `process.xlsx` + `figures/`；Agent 按 `templates/report.md` 填结果报告。样例测量文件不进仓库；测试用合成数据。

**Tech Stack:** Python 3.11+、pytest、openpyxl、numpy、matplotlib；Cursor Agent Skill（Markdown）。

**Spec:** `docs/superpowers/specs/2026-07-16-fr-curve-golden-analysis-design.md`

## Global Constraints

- 不落标准化曲线库文件；映射写在 `process.xlsx` 的 `manifest` 与报告中。
- 灵敏度标准与曲线标准互不绑定。
- 曲线金标 = `curve_rank` 第 1；辅标 = 其后 N 名；δ 步进 0.1dB。
- 灵敏度按相对中线 **0.5dB 一档**。
- 奇异值豁免：&lt;100Hz、&gt;15000Hz、**Q≥10**；先均值→剔异→重算。
- 一产品一报告；无总览页；无门禁6。
- 报告正文只呈现剔异重算后结果。
- 样例原始测量文件不复制进仓库。
- 提交信息用 conventional commits；仅在用户要求时执行 `git commit`（计划中的 Commit 步骤默认改为「暂存说明，待用户下令再 commit」）。

---

## File Structure

```
.cursor/skills/fr-curve-golden-analysis/
├── SKILL.md
├── references/layout-catalog.md
├── templates/
│   ├── intake-checklist.md
│   ├── gate1-tables.md
│   ├── product-params.md
│   └── report.md
└── scripts/
    ├── pyproject.toml          # 或 requirements.txt
    ├── fr_analysis/
    │   ├── __init__.py
    │   ├── models.py           # CurveSet, SampleCurve, AnalysisParams, MappingSpec
    │   ├── io_layouts.py       # 三种已知布局 + unknown 钩子
    │   ├── stats.py            # 归零、均值、δ排名、灵敏度分档、Q
    │   ├── outliers.py         # 偏差提名辅助（豁免规则）
    │   ├── workbook.py         # 写 process.xlsx
    │   ├── figures.py          # 规定文件名出图
    │   └── cli.py              # 命令行入口
    └── tests/
        ├── test_stats.py
        ├── test_io_layouts.py
        ├── test_outliers.py
        ├── test_workbook.py
        └── fixtures/           # 仅合成小文件
            ├── synthetic_wide.csv
            ├── synthetic_spl.txt
            └── synthetic_horizontal.tsv
```

---

### Task 1: 数据模型与核心统计（TDD）

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/fr_analysis/models.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/fr_analysis/stats.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/fr_analysis/__init__.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/requirements.txt`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_stats.py`

**Interfaces:**
- Produces:
  - `SampleCurve(sample_id: str, freq_hz: np.ndarray, spl_db: np.ndarray)`
  - `normalize_at_1khz(curve) -> SampleCurve`
  - `mean_curve(curves: list[SampleCurve]) -> SampleCurve`
  - `tightest_envelope_delta(curve, mean, f_lo, f_hi, step=0.1) -> float`
  - `rank_curves_by_envelope(curves, mean, f_lo, f_hi) -> list[tuple[str, float, float]]`  # id, delta, rms
  - `sensitivity_bins(values_db: dict[str,float], center: float, bin_width=0.5) -> dict[str, int]`  # id -> bin index
  - `estimate_peak_q(freq, spl, ...) -> float | None`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_stats.py
import numpy as np
from fr_analysis.models import SampleCurve
from fr_analysis.stats import (
    normalize_at_1khz,
    mean_curve,
    tightest_envelope_delta,
    rank_curves_by_envelope,
    sensitivity_bins,
)

def _curve(sid, offset):
    f = np.array([100.0, 1000.0, 5000.0, 10000.0])
    s = np.array([0.0, 0.0, offset, offset]) + 40.0
    return SampleCurve(sid, f, s)

def test_normalize_at_1khz_zeros_1k():
    c = normalize_at_1khz(_curve("a", 1.0))
    assert abs(float(c.spl_db[c.freq_hz == 1000.0][0])) < 1e-9

def test_envelope_prefers_tighter_delta():
    mean = mean_curve([_curve("a", 0.0), _curve("b", 0.05), _curve("c", 0.5)])
    # after normalize, offsets are relative shape; build explicit
    f = np.array([200.0, 1000.0, 2000.0])
    mean_c = SampleCurve("m", f, np.zeros(3))
    tight = SampleCurve("t", f, np.array([0.05, 0.0, -0.05]))
    loose = SampleCurve("l", f, np.array([0.3, 0.0, -0.3]))
    assert tightest_envelope_delta(tight, mean_c, 200, 2000) == 0.1
    assert tightest_envelope_delta(loose, mean_c, 200, 2000) == 0.3

def test_rank_golden_is_first():
    f = np.array([200.0, 1000.0, 2000.0])
    mean_c = SampleCurve("m", f, np.zeros(3))
    curves = [
        SampleCurve("gold", f, np.array([0.05, 0.0, -0.05])),
        SampleCurve("aux", f, np.array([0.25, 0.0, -0.25])),
    ]
    ranked = rank_curves_by_envelope(curves, mean_c, 200, 2000)
    assert ranked[0][0] == "gold"
    assert ranked[1][0] == "aux"

def test_sensitivity_bins_half_db():
    bins = sensitivity_bins({"a": -40.0, "b": -40.4, "c": -41.2}, center=-40.0, bin_width=0.5)
    assert bins["a"] == 0
    assert bins["b"] == -1 or bins["b"] == 0  # document exact rounding in impl; prefer floor toward -inf of (v-center)/0.5
```

实现约定（写进 `stats.py` 文档字符串）：`bin_index = floor((value - center) / 0.5)`（向 -∞ 取整）。修正测试：

```python
def test_sensitivity_bins_half_db():
    bins = sensitivity_bins({"a": -40.0, "b": -40.4, "c": -41.2}, center=-40.0, bin_width=0.5)
    assert bins["a"] == 0          # [-40.0, -39.5)
    assert bins["b"] == -1         # [-40.5, -40.0)
    assert bins["c"] == -3         # [-41.5, -41.0)  -> (-41.2+40)/0.5 = -2.4 -> floor -3
```

- [ ] **Step 2: 运行确认失败**

```bash
cd .cursor/skills/fr-curve-golden-analysis/scripts
pip install numpy pytest
pytest tests/test_stats.py -v
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 最小实现 `models.py` + `stats.py` + `requirements.txt`**

`requirements.txt`:

```
numpy>=1.26
openpyxl>=3.1
matplotlib>=3.8
pytest>=8.0
```

实现 `normalize_at_1khz`（插值或最近点取 1kHz）、`mean_curve`（公共频率：对每条曲线插值到公共 `freq` 网格，先用并集排序唯一频率）、`tightest_envelope_delta`（max|dev| 向上按 0.1 取整，最小 0.1）、`rank_curves_by_envelope`、`sensitivity_bins`、`estimate_peak_q`（可先返回 None 的桩，Task 3 补全）。

- [ ] **Step 4: 测试通过**

```bash
pytest tests/test_stats.py -v
```

Expected: PASS

- [ ] **Step 5: 暂存（待用户 commit）**

```bash
git add .cursor/skills/fr-curve-golden-analysis/scripts
```

---

### Task 2: 已知布局读取器（合成 fixtures）

**Files:**
- Create: `.../fr_analysis/io_layouts.py`
- Create: `.../tests/test_io_layouts.py`
- Create: `.../tests/fixtures/synthetic_wide.csv`
- Create: `.../tests/fixtures/synthetic_spl.txt`
- Create: `.../tests/fixtures/synthetic_horizontal.tsv`

**Interfaces:**
- Produces:
  - `detect_layout(path: Path) -> str`  # batch_wide_fr | spl_vertical_calsod | single_horizontal_tsv | unknown
  - `load_curves(path: Path, mapping: dict | None = None) -> list[SampleCurve]`
  - `load_sensitivity_row(path) -> dict[str, float] | None`  # wide 表 *1000Hz* 行

**合成 fixtures 内容约定：**

`synthetic_spl.txt`（仿 CALSOD）:

```
CALSOD
Frequenzgang TEST 1
2
0.0
0.0
1.0
0
   100.00  -40.00    0.00
  1000.00  -38.00    0.00
  5000.00  -37.00    0.00
```

`synthetic_horizontal.tsv`:

```
100.00	1000.00	5000.00
-40.00	-38.00	-37.00
```

`synthetic_wide.csv`（简化版 wide：第1列频率，其余为样机）:

```
freq,1,2
100,-40.1,-39.5
1000,-38.0,-37.8
5000,-37.0,-36.5
```

- [ ] **Step 1: 写失败测试** `test_io_layouts.py` 覆盖三种 detect + load 点数/sample_id。
- [ ] **Step 2: pytest 确认 FAIL**
- [ ] **Step 3: 实现 `io_layouts.py`**（CSV/TSV/文本；xlsx 用 openpyxl，wide 识别含 `Curves` 或首列频率启发式）
- [ ] **Step 4: pytest PASS**
- [ ] **Step 5: git add（待 commit）**

---

### Task 3: 奇异值辅助（豁免规则）

**Files:**
- Create: `.../fr_analysis/outliers.py`
- Create: `.../tests/test_outliers.py`
- Modify: `.../fr_analysis/stats.py`（补全 `estimate_peak_q`）

**Interfaces:**
- Produces:
  - `band_deviation(curve, mean, f_lo=100.0, f_hi=15000.0) -> float`  # max |dev| in band
  - `propose_outliers(curves, mean, rms_threshold: float) -> list[dict]`  
    每项: `{sample_id, reason, max_dev, exempt_high_q: bool}`  
    规则：只在 100–15000Hz 计偏差；若该样在带内最大偏差由 Q≥10 的峰/谷主导则 `exempt_high_q=True` 且默认不进「建议剔除」列表（仍可出现在 review 表）。

- [ ] **Step 1–4:** TDD 实现；用人工构造「宽带偏高」vs「窄尖峰 Q≥10」两条曲线断言只有前者被 propose。
- [ ] **Step 5:** git add

---

### Task 4: 写 process.xlsx + 规定图

**Files:**
- Create: `.../fr_analysis/workbook.py`
- Create: `.../fr_analysis/figures.py`
- Create: `.../tests/test_workbook.py`

**Interfaces:**
- Produces:
  - `write_process_workbook(out_dir: Path, payload: AnalysisPayload) -> Path`  # 返回 process.xlsx 路径
  - `write_figures(out_dir: Path, payload: AnalysisPayload) -> list[Path]`
- `AnalysisPayload` 字段至少含: manifest dict、curves、excluded ids、mean_before、mean_after、curve_rank、sensitivity table、params。

**Sheet 名（与设计一致）：**  
`manifest`, `sensitivity_1000hz`, `mean_before_outlier`, `outlier_review`, `mean_after_outlier`, `curve_rank`, `sensitivity_standards`

**图文件名：**
- `figures/fig_sensitivity_0p5dB_overview.png`
- `figures/fig_curve_golden_overlay.png`
- `figures/fig_sensitivity_band_*.png`（附录分档，按出现过的 bin 生成）

- [ ] **Step 1:** 测试：临时目录写出 xlsx，用 openpyxl 断言 sheet 存在；断言 png 文件存在。
- [ ] **Step 2–4:** 实现并 PASS
- [ ] **Step 5:** git add

---

### Task 5: CLI 入口

**Files:**
- Create: `.../fr_analysis/cli.py`
- Create: `.../tests/test_cli.py`

**Interfaces:**
- CLI:

```bash
python -m fr_analysis.cli run \
  --input-dir <dir> \
  --mapping-json <file> \
  --params-json <file> \
  --excluded-json <file> \
  --out-dir <dir> \
  --aux-count 3
```

- `mapping.json` 最小 schema:

```json
{
  "product": "456",
  "layout": "batch_wide_fr",
  "files": [{"path": "relative/or/abs", "layout": "batch_wide_fr"}]
}
```

- `params.json`:

```json
{
  "f_lo": 20.0,
  "f_hi": 20000.0,
  "sensitivity_mode": "batch_mean",
  "design_1khz_db": null,
  "aux_count": 3
}
```

- `excluded.json`: `["id1", "id2"]`

流程：`load` → mean_before →（excluded 已由门禁3确认，CLI 不自动删）→ mean_after on remaining → rank → sensitivity bins → workbook + figures。

注意：CLI **不**做门禁对话；只计算。奇异值提名可由另条子命令：

```bash
python -m fr_analysis.cli propose-outliers --mapping-json ... --out-json outliers.json
```

- [ ] **Step 1–4:** TDD：用 fixtures 跑 `run`，断言 out_dir 下有 process.xlsx 与至少 2 张 png。
- [ ] **Step 5:** git add

---

### Task 6: Skill 文档包（SOP + 模板 + 布局目录）

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/SKILL.md`
- Create: `.cursor/skills/fr-curve-golden-analysis/references/layout-catalog.md`
- Create: `.cursor/skills/fr-curve-golden-analysis/templates/intake-checklist.md`
- Create: `.cursor/skills/fr-curve-golden-analysis/templates/gate1-tables.md`
- Create: `.cursor/skills/fr-curve-golden-analysis/templates/product-params.md`
- Create: `.cursor/skills/fr-curve-golden-analysis/templates/report.md`

**SKILL.md frontmatter:**

```yaml
---
name: fr-curve-golden-analysis
description: Use when analyzing microphone or FR frequency-response measurement batches to select curve golden/auxiliary standards, sensitivity 0.5dB bins, check consistency, or produce measurement reports from folders of SPL/XLS/CSV curve data.
---
```

**SKILL.md 正文必须包含（与设计逐条对齐）：**
1. Intake 收口（提示词不完整也要启动）
2. 步骤1 探查剧本 + 门禁1 表 A–D（禁止干问列名）
3. 多产品拆分；一产品一报告；无总览
4. 门禁2 参数（无贴均值公差填写）
5. 步骤3 先均值→奇异值→重算；豁免 &lt;100、&gt;15k、Q≥10
6. 调用 `propose-outliers` / `run` 的确切命令示例（相对 skill 内 scripts 路径）
7. 双轨标准；曲线 δ 排名；灵敏度 0.5dB
8. 报告合同：固定章节、必出图文件名、数字只来自 process.xlsx
9. 硬停门禁列表 1–5（无门禁6）

`layout-catalog.md`：三种已知布局的字段级说明（对照设计里的 456_FR / SPL / smile 行为，不复制原文件）。

`templates/report.md`：空骨架与 §9 章节一致。

- [ ] **Step 1:** 写齐上述文件（无测试代码；人工对照设计文档 checklist）。
- [ ] **Step 2:** 自检：打开设计文档 §12 成功标准，逐条在 SKILL.md 找到对应段落。
- [ ] **Step 3:** git add

---

### Task 7: 端到端冒烟（合成数据）

**Files:**
- Create: `.../tests/test_e2e_smoke.py`

- [ ] **Step 1:** 测试创建临时目录，放入三种 fixtures，写 mapping/params/excluded，调用 CLI `run`，再断言：
  - `curve_rank` 第一行存在
  - `report` 不在脚本职责内（Agent 写）；脚本侧只检 xlsx/figures
- [ ] **Step 2:** `pytest tests/ -v` 全绿
- [ ] **Step 3:** 在 README（可选，仅 scripts 下 `README.md` 5～10 行：如何 pip install 与跑 cli）——若要保持仓库根干净，只写 `scripts/README.md`
- [ ] **Step 4:** 请用户审查；**用户明确要求后再 commit**

---

## Spec Coverage Self-Check

| 设计要点 | Task |
|----------|------|
| Intake / @Skill | Task 6 |
| 布局探查 + 门禁1 UI | Task 6 + Task 2 |
| 多产品 / 一产品一报告 | Task 6 |
| 门禁2 参数 | Task 6 + Task 5 params.json |
| 先均值剔异重算 + 豁免 | Task 3 + Task 5 + Task 6 |
| 曲线 δ 排名金标/辅标 | Task 1 + Task 5 |
| 灵敏度 0.5dB 双轨 | Task 1 + Task 4 + Task 6 |
| process.xlsx sheets | Task 4 |
| 报告合同与图 | Task 4 figures + Task 6 template |
| 无总览 / 无门禁6 / 样例不进库 | Task 6 + fixtures 仅合成 |
| 脚本「接口」= CLI | Task 5 |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-16-fr-curve-golden-analysis.md`.

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每任务新开子代理，任务间复查  
2. **Inline Execution** — 本会话按 executing-plans 连续做，设检查点  

你要哪一种？也可以说「先别写代码，我再改计划」。
