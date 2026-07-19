# SP3: C 走势分析（分类 + 峰谷）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 `fr-curve-directivity-analysis`（C）加走势分析：按角度对 delta 曲线无监督聚类 → 类均值峰谷（含 Q）→ LLM 勾选 → 报告第 5 节（分类表 + 类均值标注图 + 峰谷表 + 类内叠图），并配 L1/L2/L3 机械验证。

**Architecture:** 新增 `run_cluster.py`（欧氏距离矩阵 + average-linkage 层次聚类 + 轮廓系数选 k → dist/suggest/meta/final）与 `run_peaks.py`（类均值 + scipy find_peaks → candidates）。新增 `render_trend_figures.py` 出走势图。`compose_html.py` 加第 5 节 + L3。LLM 只改 `cluster_final` 与 `selected`（SOP/references 约束）。A/B/shared 与既有 C 分析脚本业务逻辑不动。

**Tech Stack:** Python 3.10+，openpyxl，numpy，scipy，matplotlib，pytest，Jinja2。

## Global Constraints

- 范围：仅 C（`.cursor/skills/fr-curve-directivity-analysis/`）；A/B/shared 不动。
- 不改业务逻辑：`run_deltas.py` / `run_freq_bins.py` / `run_consistency.py` / `render_figures.py`（可被 compose/SOP 并列调用，但不改其行为）。
- 命令行只带 `--params <产出目录>/params.json`。
- 数值只由脚本写 xlsx；LLM 不算数。
- 退出码：`0` 成功；`2` 前置/非法 params；`3` L2/L3 自检失败。
- 编码：UTF-8；`ensure_utf8_stdio()`；中文不进 CLI 参数。
- TDD：失败测试 → 最小实现 → 通过 → commit。
- 测试目录：`cd .cursor\skills\fr-curve-directivity-analysis\scripts && python -m pytest tests/... -v`
- Spec 真源：`docs/superpowers/specs/2026-07-19-sp3-trend-analysis-design.md`

## File Structure

**新增：**
- `scripts/run_cluster.py`
- `scripts/run_peaks.py`
- `scripts/render_trend_figures.py`
- `scripts/tests/test_run_cluster.py`
- `scripts/tests/test_run_peaks.py`
- `scripts/tests/test_compose_trend.py`
- `references/cluster-llm-rules.md`

**改动：**
- `scripts/requirements.txt` — 加 `scipy`、`numpy`
- `scripts/compose_html.py` — 走势节 + L3
- `scripts/templates/report.html.j2` — 节重编号 1–6
- `SKILL.md` — 步骤 3.4–3.7
- `references/params.template.json`
- `references/data-contract-sheets.md`
- `references/report-outline.md`
- `references/fill-chat-summary.md`

**任务依赖：** Task 1（deps）→ 2–5（cluster）→ 6–8（peaks）→ 9（render）→ 10–11（compose）→ 12–13（docs）

---

## Task 1: 依赖 + params 默认字段

**Files:**
- Modify: `scripts/requirements.txt`
- Modify: `references/params.template.json`
- Test: `scripts/tests/test_params_sp3.py`（新建，轻量）

**Interfaces:**
- Produces: `scipy`/`numpy` 可 import；params 模板含 `cluster_k_max=5`, `peak_prominence_db=1.0`, `peak_min_octave`≈0.333333, `peak_include_q=true`

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "references" / "params.template.json"


def test_params_template_has_sp3_fields():
    data = json.loads(REF.read_text(encoding="utf-8"))
    assert data["cluster_k_max"] == 5
    assert data["peak_prominence_db"] == 1.0
    assert abs(float(data["peak_min_octave"]) - (1.0 / 3.0)) < 1e-9
    assert data["peak_include_q"] is True


def test_scipy_importable():
    import scipy  # noqa: F401
    from scipy.signal import find_peaks  # noqa: F401
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_params_sp3.py -v`  
Expected: FAIL（缺字段和/或缺 scipy）

- [ ] **Step 3: 改 requirements + params.template.json**

`requirements.txt` 追加：
```
numpy>=1.24
scipy>=1.11
```

`params.template.json` 在 `focus_freqs` 后追加：
```json
  "cluster_k_max": 5,
  "peak_prominence_db": 1.0,
  "peak_min_octave": 0.3333333333,
  "peak_include_q": true
```

- [ ] **Step 4: 安装依赖并跑通**

Run: `pip install -r requirements.txt`  
Run: `python -m pytest tests/test_params_sp3.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/requirements.txt .cursor/skills/fr-curve-directivity-analysis/references/params.template.json .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_params_sp3.py
git commit -m "chore(C): add scipy/numpy and SP3 params defaults for trend analysis"
```

---

## Task 2: run_cluster 核心 — 距离矩阵 + k=1

**Files:**
- Create: `scripts/run_cluster.py`
- Create: `scripts/tests/test_run_cluster.py`

**Interfaces:**
- Consumes: `delta_<tag>`, `f_lo_hz`, `f_hi_hz`, `cluster_k_max`
- Produces: `cluster_dist_<tag>`, `cluster_suggest_<tag>`, `cluster_meta_<tag>`, `cluster_final_<tag>`（若不存在）；`main(argv) -> int`

- [ ] **Step 1: 写失败测试 `test_two_identical_samples_k1`**

```python
# -*- coding: utf-8 -*-
"""Tests for run_cluster: Euclidean clustering of delta curves."""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from conftest import build_angle_workbook, write_params
from run_deltas import main as run_deltas_main
from run_cluster import main as run_cluster_main


def _prep(tmp_path: Path, *, axis_cols, angle_cols, extra=None):
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        extra={"focus_freqs": [1000], "cluster_k_max": 5, **(extra or {})},
    )
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0, 4000.0],
        values_by_angle={"axis": axis_cols, "90": angle_cols},
    )
    run_deltas_main(["--params", str(out / "params.json")])
    return out


def test_two_identical_samples_k1(tmp_path):
    # identical deltas → one cluster
    axis = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    ang = [[2.0, 3.0, 4.0], [2.0, 3.0, 4.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang)

    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    assert "cluster_dist_90" in wb.sheetnames
    assert "cluster_suggest_90" in wb.sheetnames
    assert "cluster_meta_90" in wb.sheetnames
    assert "cluster_final_90" in wb.sheetnames

    ws_d = wb["cluster_dist_90"]
    assert float(ws_d.cell(2, 2).value) == 0.0  # diagonal
    assert float(ws_d.cell(2, 3).value) == 0.0  # identical

    ws_s = wb["cluster_suggest_90"]
    assert int(ws_s.cell(2, 2).value) == 1
    assert int(ws_s.cell(3, 2).value) == 1

    ws_m = wb["cluster_meta_90"]
    # header + rows for k; chosen_k == 1
    chosen = [r for r in range(2, ws_m.max_row + 1) if str(ws_m.cell(r, 3).value) == "yes"]
    assert len(chosen) == 1
    assert int(ws_m.cell(chosen[0], 1).value) == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_run_cluster.py::test_two_identical_samples_k1 -v`  
Expected: `ModuleNotFoundError: No module named 'run_cluster'`

- [ ] **Step 3: 写最小 `run_cluster.py`**

实现要点（完整代码由实现者按 spec §5.1 写出）：
- `_euclid(a, b)`：只对两端非 None 求和
- `_band_mask(freqs, f_lo, f_hi)`
- `_replace_sheet`
- `n_clusterable < 1` → exit 2
- `n_clusterable == 1` 或全距离≈0 时 k=1 路径
- 写 dist（样机×样机）、suggest（sample, cluster_id, dist_to_center）、meta（k, silhouette, chosen）、无 final 则复制
- k=1：silhouette 写 `"N/A"`，`chosen=yes`
- average linkage + silhouette 可先只实现 k=1 路径让本测试过；多 k 在 Task 3

最小可过本测试的实现：强制 k=1 给全体，距离矩阵仍要算对。

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_run_cluster.py::test_two_identical_samples_k1 -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_cluster.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_cluster.py
git commit -m "feat(C): add run_cluster distance matrix and k=1 path"
```

---

## Task 3: run_cluster — 层次聚类 + 轮廓系数选 k

**Files:**
- Modify: `run_cluster.py`
- Test: `tests/test_run_cluster.py`（追加）

**Interfaces:**
- Uses: `scipy.cluster.hierarchy.linkage` / `fcluster`；预计算欧氏 condensed 距离
- Produces: `k≥2` 时选 silhouette 最大；并列取更小 k

- [ ] **Step 1: 追加失败测试**

```python
def test_two_clear_groups_k2(tmp_path):
    # S01 delta ~ +1 everywhere; S02 delta ~ +10 everywhere → 2 clusters
    axis = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    ang = [[1.0, 1.0, 1.0], [10.0, 10.0, 10.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang)

    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    ws_m = wb["cluster_meta_90"]
    chosen = [r for r in range(2, ws_m.max_row + 1) if str(ws_m.cell(r, 3).value) == "yes"]
    assert int(ws_m.cell(chosen[0], 1).value) == 2

    ws_s = wb["cluster_suggest_90"]
    ids = {int(ws_s.cell(2, 2).value), int(ws_s.cell(3, 2).value)}
    assert ids == {1, 2}
```

- [ ] **Step 2: 跑测试确认失败**（若 Task 2 强制 k=1）

Run: `python -m pytest tests/test_run_cluster.py::test_two_clear_groups_k2 -v`  
Expected: FAIL（chosen k != 2）

- [ ] **Step 3: 实现 k 搜索**

```python
# sketch — implement fully in run_cluster.py
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
import numpy as np

def _silhouette_precomputed(dist: np.ndarray, labels: np.ndarray) -> float:
    # classic silhouette using precomputed pairwise distances; return mean
    ...

def _choose_k(dist: np.ndarray, k_max: int) -> tuple[int, list[tuple[int, float | str]]]:
    n = dist.shape[0]
    rows = []
    best_k, best_s = 1, float("-inf")
    condensed = squareform(dist, checks=False)
    for k in range(1, min(k_max, n) + 1):
        if k == 1:
            rows.append((1, "N/A"))
            continue
        Z = linkage(condensed, method="average")
        labels = fcluster(Z, t=k, criterion="maxclust")
        s = _silhouette_precomputed(dist, labels)
        rows.append((k, s))
        if s > best_s or (s == best_s and k < best_k):
            best_s, best_k = s, k
    if best_s == float("-inf"):
        best_k = 1
    return best_k, rows
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_run_cluster.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_cluster.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_cluster.py
git commit -m "feat(C): select cluster k via average-linkage silhouette"
```

---

## Task 4: run_cluster — final 不覆盖 + 缺 delta exit 2 + 非法 params

**Files:**
- Modify: `run_cluster.py`
- Test: `tests/test_run_cluster.py`（追加）

- [ ] **Step 1: 追加测试**

```python
def test_final_not_overwritten(tmp_path):
    axis = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    ang = [[2.0, 3.0, 4.0], [2.0, 3.0, 4.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang)
    run_cluster_main(["--params", str(out / "params.json")])
    wb = load_workbook(out / "process.xlsx")
    ws = wb["cluster_final_90"]
    ws.cell(2, 3).value = "自定义类"
    wb.save(out / "process.xlsx")

    run_cluster_main(["--params", str(out / "params.json")])
    wb = load_workbook(out / "process.xlsx")
    assert wb["cluster_final_90"].cell(2, 3).value == "自定义类"


def test_missing_delta_exit2(tmp_path):
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        extra={"cluster_k_max": 5},
    )
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0],
        values_by_angle={
            "axis": [[1.0, 2.0], [1.0, 2.0]],
            "90": [[2.0, 3.0], [3.0, 4.0]],
        },
    )
    # no run_deltas
    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 2


def test_invalid_cluster_k_max_exit2(tmp_path):
    axis = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    ang = [[2.0, 3.0, 4.0], [2.0, 3.0, 4.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang, extra={"cluster_k_max": 0})
    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 2
```

- [ ] **Step 2: 实现校验与 final 保留逻辑（若尚未有）**

- [ ] **Step 3: 跑通**

Run: `python -m pytest tests/test_run_cluster.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_cluster.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_cluster.py
git commit -m "feat(C): preserve cluster_final on rerun; gate missing delta and bad k_max"
```

---

## Task 5: run_cluster L2 自检（exit 3）

**Files:**
- Modify: `run_cluster.py`（`_verify_cluster_sheets`）
- Test: `tests/test_run_cluster.py`

- [ ] **Step 1: 追加测试**

```python
def test_cluster_verification_pass(tmp_path, capsys):
    axis = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    ang = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang)
    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 0
    assert "VERIFICATION OK" in capsys.readouterr().out


def test_cluster_verification_fail_exit3(tmp_path, monkeypatch):
    axis = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    ang = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis, angle_cols=ang)
    import run_cluster
    def bad_verify(*a, **k):
        raise ValueError("sabotage")
    monkeypatch.setattr(run_cluster, "_verify_cluster_sheets", bad_verify)
    rc = run_cluster_main(["--params", str(out / "params.json")])
    assert rc == 3
    wb = load_workbook(out / "process.xlsx")
    assert "cluster_dist_90" not in wb.sheetnames
    assert "cluster_suggest_90" not in wb.sheetnames
    assert "cluster_meta_90" not in wb.sheetnames
```

- [ ] **Step 2: 实现 `_verify_cluster_sheets`**

检查：dist 对称、对角≈0；suggest 样机集合完整；meta 恰有一行 `chosen=yes`；chosen k 在范围内。失败删本角 dist/suggest/meta（及本跑新建的 final）→ exit 3。

- [ ] **Step 3: 跑通 + Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_cluster.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_cluster.py
git commit -m "feat(C): add L2 self-check for run_cluster (exit 3 + delete bad sheets)"
```

---

## Task 6: run_peaks — 类均值 + 候选峰（无 Q 也可先）

**Files:**
- Create: `scripts/run_peaks.py`
- Create: `scripts/tests/test_run_peaks.py`

**Interfaces:**
- Consumes: `cluster_final_<tag>`, `delta_<tag>`, `peak_prominence_db`, `peak_min_octave`
- Produces: `class_mean_<tag>`, `peak_candidates_<tag>`；`main(argv) -> int`

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from openpyxl import load_workbook
from conftest import build_angle_workbook, write_params
from run_deltas import main as run_deltas_main
from run_cluster import main as run_cluster_main
from run_peaks import main as run_peaks_main


def _prep_clustered(tmp_path: Path):
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        f_lo_hz=100.0,
        f_hi_hz=10000.0,
        extra={
            "cluster_k_max": 5,
            "peak_prominence_db": 0.5,
            "peak_min_octave": 0.1,
            "peak_include_q": True,
        },
    )
    # dense-ish freqs for a visible peak at 1000
    freqs = [100.0, 300.0, 1000.0, 3000.0, 8000.0]
    axis = [[0.0] * 5, [0.0] * 5]
    # both samples: peak at 1000 (+5)
    ang = [[0.0, 0.5, 5.0, 0.5, 0.0], [0.0, 0.5, 5.0, 0.5, 0.0]]
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90"],
        samples=["S01", "S02"],
        freqs=freqs,
        values_by_angle={"axis": axis, "90": ang},
    )
    run_deltas_main(["--params", str(out / "params.json")])
    run_cluster_main(["--params", str(out / "params.json")])
    return out


def test_class_mean_and_peak_candidate(tmp_path):
    out = _prep_clustered(tmp_path)
    rc = run_peaks_main(["--params", str(out / "params.json")])
    assert rc == 0
    wb = load_workbook(out / "process.xlsx")
    assert "class_mean_90" in wb.sheetnames
    assert "peak_candidates_90" in wb.sheetnames
    ws_p = wb["peak_candidates_90"]
    # header: cluster_id, kind, freq_hz, amplitude_db, q, prominence_db, selected
    kinds = [str(ws_p.cell(r, 2).value) for r in range(2, ws_p.max_row + 1)]
    assert "peak" in kinds
    freqs = [float(ws_p.cell(r, 3).value) for r in range(2, ws_p.max_row + 1)
             if str(ws_p.cell(r, 2).value) == "peak"]
    assert any(abs(f - 1000.0) / 1000.0 < 0.05 for f in freqs)
    assert all(str(ws_p.cell(r, 7).value) == "no" for r in range(2, ws_p.max_row + 1))
```

- [ ] **Step 2: 跑失败 → 实现 `run_peaks.py`（find_peaks + 谷；Q 可先写 N/A）→ 跑通 → Commit**

```bash
git commit -m "feat(C): add run_peaks class mean and peak/valley candidates"
```

---

## Task 7: run_peaks — Q 计算 + selected 保留 + gates

**Files:**
- Modify: `run_peaks.py`
- Test: `tests/test_run_peaks.py`

- [ ] **Step 1: 追加测试**

```python
def test_missing_final_exit2(tmp_path):
    out = _prep_clustered(tmp_path)
    wb = load_workbook(out / "process.xlsx")
    del wb["cluster_final_90"]
    wb.save(out / "process.xlsx")
    assert run_peaks_main(["--params", str(out / "params.json")]) == 2


def test_selected_preserved_on_rerun(tmp_path):
    out = _prep_clustered(tmp_path)
    run_peaks_main(["--params", str(out / "params.json")])
    wb = load_workbook(out / "process.xlsx")
    ws = wb["peak_candidates_90"]
    # select first peak row
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(r, 2).value) == "peak":
            ws.cell(r, 7).value = "yes"
            old_f = float(ws.cell(r, 3).value)
            break
    wb.save(out / "process.xlsx")
    run_peaks_main(["--params", str(out / "params.json")])
    wb = load_workbook(out / "process.xlsx")
    ws = wb["peak_candidates_90"]
    found = False
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(r, 2).value) == "peak" and str(ws.cell(r, 7).value) == "yes":
            assert abs(float(ws.cell(r, 3).value) - old_f) / old_f <= 0.005
            found = True
    assert found


def test_invalid_prominence_exit2(tmp_path):
    out = _prep_clustered(tmp_path)
    import json
    p = json.loads((out / "params.json").read_text(encoding="utf-8"))
    p["peak_prominence_db"] = 0
    (out / "params.json").write_text(json.dumps(p), encoding="utf-8")
    assert run_peaks_main(["--params", str(out / "params.json")]) == 2
```

- [ ] **Step 2: 实现 `_compute_q`（FWHM；失败 → `"N/A"`）与 selected 合并（0.5% 规则）**

- [ ] **Step 3: 跑通 + Commit**

```bash
git commit -m "feat(C): peak Q, selected retention, and peaks param gates"
```

---

## Task 8: run_peaks L2 自检

**Files:**
- Modify: `run_peaks.py`
- Test: `tests/test_run_peaks.py`

- [ ] **Step 1: 追加 `test_peaks_verification_pass` + `test_peaks_verification_fail_exit3`（monkeypatch `_verify_peak_sheets`）**

- [ ] **Step 2: 实现自检（均值列↔final 类；freq 在带内；selected∈{yes,no}）；失败删 class_mean/peak_candidates → exit 3**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(C): add L2 self-check for run_peaks (exit 3)"
```

---

## Task 9: render_trend_figures.py

**Files:**
- Create: `scripts/render_trend_figures.py`
- Create: `scripts/tests/test_render_trend_figures.py`

**Interfaces:**
- Consumes: `class_mean_*`, `peak_candidates_*`（selected）、`delta_*`、`cluster_final_*`
- Produces: `figures/走势_类均值_<tag>.png`；`figures/走势_类内叠图_<tag>_类<id>.png`；缺 final/candidates → exit 2

- [ ] **Step 1: 测试 — 跑 deltas→cluster→peaks 后 render，断言 PNG 存在；删 final 后 exit 2**

- [ ] **Step 2: 实现出图（复用 `render_figures.py` 的字体/log 轴辅助模式；中文文件名）**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(C): render trend class-mean and per-class overlay figures"
```

---

## Task 10: compose_html 走势节

**Files:**
- Modify: `compose_html.py`
- Modify: `templates/report.html.j2`
- Create: `tests/test_compose_trend.py`

**Interfaces:**
- `build_trend_html(output_dir, params) -> str`；缺 sheet → `SystemExit(2)`
- 模板：节 1–6，第 5 节「走势分析」；标题由模板提供

- [ ] **Step 1: 测试 `test_render_trend_section`** — HTML 含「走势分析」、分类样机名、峰谷表头（在 selected 后）

准备：`_prep` 跑完 cluster+peaks，并把至少一行 `selected=yes`，再 `compose_report_html`。

- [ ] **Step 2: 实现 `build_trend_html` + 模板插入 + `--trend-note` CLI 可选**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(C): render trend analysis section in directivity report"
```

---

## Task 11: compose L3 走势自检 + 缺 sheet exit 2

**Files:**
- Modify: `compose_html.py`（扩展 `_verify_report_html` 或加 `_verify_trend_html`）
- Test: `tests/test_compose_trend.py`

- [ ] **Step 1: `test_trend_exit2_when_sheet_missing` + `test_trend_verification_fail_exit3`（破坏「走势分析」或分类表标记）**

- [ ] **Step 2: L3 检查：含「走势分析」；每非轴向角有分类表；若有 selected 则峰谷表含列「中心频率」「幅度」「Q」**

注意：与现有 freq_bins L3 共存；`focus_freqs` 空时仍要验走势（SP3 默认总跑）。

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(C): L3 report self-check for trend section (exit 3)"
```

---

## Task 12: SKILL.md SOP

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 步骤 3 执行顺序改为 3.1→…→3.8；插入 3.4 run_cluster、3.5 LLM 微调、3.6 run_peaks、3.7 LLM 勾选；原短结顺延**

- [ ] **Step 2: 步骤 4 加 `render_trend_figures.py` 与 `--trend-note`；铁律/交付物含 cluster/peak sheets**

- [ ] **Step 3: 目检无断号 → Commit**

```bash
git commit -m "docs(C): add cluster/peaks SOP steps 3.4-3.7 and trend report notes"
```

---

## Task 13: references 同步

**Files:**
- Modify: `data-contract-sheets.md`, `report-outline.md`, `fill-chat-summary.md`
- Create: `cluster-llm-rules.md`

- [ ] **Step 1: 按 spec §4 / §5.3 / §6 / §7 写入合同与 LLM 规则；报告大纲第 5 章 + 自检 J/K；短结必报类数与勾选峰谷数**

- [ ] **Step 2: Commit**

```bash
git commit -m "docs(C): sync references for trend analysis sheets, outline, and LLM rules"
```

---

## 计划自审

**1. 规格覆盖（spec §9）：**

| 验收项 | 任务 |
|--------|------|
| dist/suggest/meta + 自动 final | Task 2–4 |
| 欧氏不中心化 + 轮廓选 k | Task 2–3 |
| final 不覆盖 | Task 4 |
| class_mean + candidates + Q | Task 6–7 |
| selected 仅报告/图 | Task 7, 9–10 |
| 报告第 5 节四块 | Task 9–10 |
| exit 2/3 | Task 4–5, 7–8, 11 |
| A/B/shared 不动 | Global Constraints |
| pytest 绿 | 全任务 |

**2. 占位扫描：** 无 TBD；聚类/峰谷核心算法在 Task 2–3/6–7 给出可实现草图与断言。

**3. 类型一致性：** `main(argv)->int`；sheet 名 `cluster_*` / `class_mean_*` / `peak_candidates_*` 全程一致；selected 字符串 `yes`/`no`。

---

## 执行交接

计划已保存到 `docs/superpowers/plans/2026-07-19-sp3-trend-analysis.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** — 每 Task 新 subagent，任务间 review  

**2. Inline Execution** — 本会话按 executing-plans 批量执行，带 checkpoint  

选哪种？
