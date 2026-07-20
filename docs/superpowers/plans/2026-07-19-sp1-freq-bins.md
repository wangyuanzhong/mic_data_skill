# SP1: C 频点差值分档 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 `fr-curve-directivity-analysis`（C）加"频点差值分档"能力：对用户关注的频点（默认 1000Hz，可加），按 1dB 一档统计各角度差值曲线（angle − axial）的分布，写 xlsx 两张 sheet/角度，报告渲染对应节，并配 3 层机械验证。

**Architecture:** 新增 `run_freq_bins.py`（只传 `--params`，读 `delta_<tag>` sheet → 算 1dB 分档 → 写 `freq_bins_<tag>` + `freq_bins_summary_<tag>` → L2 读回自检，失败删坏 sheet + exit 3）。`compose_html.py` 加一节（从 params.json 读 `focus_freqs`，只读 xlsx 渲染，L3 自检）。SOP 插步骤3b。A/B/shared 不动。

**Tech Stack:** Python 3.10+，openpyxl，pytest，Jinja2，PowerShell。

## Global Constraints

- 范围：仅 C（`e:\vibe\mic_data_skill\.cursor\skills\fr-curve-directivity-analysis\`）；A/B/shared 任何文件不动。
- C 现有脚本不动：`run_deltas.py` / `run_consistency.py` / `render_figures.py` / `quantize.py` / `angle_sheets.py` / `params_io.py` / `compose_pdf.py`。
- 命令行只带 `--params <产出目录>/params.json`（对齐现有脚本约定）。
- 一切数值计算由脚本对 xlsx 处理；compose_html 只读 xlsx 渲染，不算数。
- 退出码：`0` 成功/合法跳过；`2` 前置缺失（硬 gate）；`3` 验证失败（自检）。
- 编码：所有文件 UTF-8；脚本首行 `# -*- coding: utf-8 -*-`；用 `ensure_utf8_stdio()`。
- 中文/特殊字符不进命令行参数（PowerShell 编码问题）；focus_freqs 从 params.json 读。
- TDD：先写失败测试 → 跑确认失败 → 最小实现 → 跑确认通过 → commit。
- 测试从 `scripts/tests/` 目录跑：`cd .cursor\skills\fr-curve-directivity-analysis\scripts && python -m pytest tests/test_run_freq_bins.py -v`。

## File Structure

**新增文件**：
- `scripts/run_freq_bins.py` — 核心脚本：读 params.focus_freqs + delta sheets → 算 1dB 分档 → 写两张 sheet/角度 → L2 自检。
- `scripts/tests/test_run_freq_bins.py` — run_freq_bins 单元测试。
- `scripts/tests/test_compose_freq_bins.py` — compose_html 频点节单元测试。

**改动文件**：
- `scripts/compose_html.py` — 加 `build_freq_bins_html()` + 集成到 `compose_report_html()` + L3 自检 + 读 params.focus_freqs。
- `scripts/templates/report.html.j2` — 在差值节和一致性节之间插"频点差值分档"节。
- `SKILL.md` — intake 加问 focus_freqs + 步骤3b + 报告节说明。
- `references/params.template.json` — 加 `focus_freqs` 字段（默认 `[1000]`）。
- `references/data-contract-sheets.md` — 加 `freq_bins_<tag>` 和 `freq_bins_summary_<tag>` 两节。
- `references/report-outline.md` — 加频点节大纲 + 自检项。
- `references/fill-chat-summary.md` — 加 focus_freqs intake 填法。

**任务依赖**：Task 1-9（run_freq_bins 核心）→ Task 10（L2 自检）→ Task 11-14（compose_html）→ Task 15（SKILL.md）→ Task 16（references）。

---

## Task 1: run_freq_bins.py 核心骨架（基础分档）

**Files:**
- Create: `.cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py`
- Test: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py`

**Interfaces:**
- Consumes: `params.json`（`focus_freqs` / `angles` / `axial_angle` / `f_lo_hz` / `f_hi_hz`），`delta_<tag>` sheet（由 `run_deltas.py` 产出）
- Produces: `freq_bins_<tag>` + `freq_bins_summary_<tag>` sheet；`main(argv) -> int`（0/2/3）

- [ ] **Step 1: 写失败测试 `test_basic_two_freqs`**

```python
# -*- coding: utf-8 -*-
"""Tests for run_freq_bins: 1dB binning of per-angle delta at focus freqs."""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from conftest import build_angle_workbook, write_params
from run_deltas import main as run_deltas_main
from run_freq_bins import main as run_freq_bins_main


def _prep(tmp_path: Path, *, axis_cols, angle_cols, focus_freqs):
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        extra={"focus_freqs": focus_freqs},
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


def test_basic_two_freqs(tmp_path):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]  # S01 +1, S02 +3 everywhere
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000, 4000])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    assert "freq_bins_90" in wb.sheetnames
    assert "freq_bins_summary_90" in wb.sheetnames

    ws_d = wb["freq_bins_90"]
    assert ws_d.max_column == 1 + 2 * 2  # 样机 + 2 freqs × (差值, 档位)
    assert ws_d.max_row == 1 + 2  # header + 2 samples
    assert str(ws_d.cell(1, 1).value) == "样机"
    assert "1000Hz" in str(ws_d.cell(1, 2).value)
    # S01 delta=+1 -> bin "1~2"; S02 delta=+3 -> bin "3~4"
    assert str(ws_d.cell(2, 3).value) == "1~2"
    assert str(ws_d.cell(3, 3).value) == "3~4"

    ws_s = wb["freq_bins_summary_90"]
    assert ws_s.max_column == 2 * 2
    assert "分组" in str(ws_s.cell(1, 1).value)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd .cursor\skills\fr-curve-directivity-analysis\scripts && python -m pytest tests/test_run_freq_bins.py::test_basic_two_freqs -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_freq_bins'`

- [ ] **Step 3: 写最小实现 `run_freq_bins.py`**

```python
# -*- coding: utf-8 -*-
"""run_freq_bins.py — write freq_bins_<tag> + freq_bins_summary_<tag> per non-axial angle.

For each non-axial angle's delta_<tag> sheet, for each focus frequency, find the
nearest frequency, take per-sample deltas, bin into 1dB left-closed right-open
bins, and write a detail sheet and a summary sheet.

Usage:
    python run_freq_bins.py --params <output_dir>/params.json
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from angle_sheets import normalize_angle_tag, read_angle_sheet
from params_io import load_params, resolve_under_output
from utf8_boot import ensure_utf8_stdio


def _format_hz(ff: float) -> str:
    if ff == int(ff):
        return str(int(ff))
    return str(ff)


def _nearest_freq_index(freqs: list[float], target: float) -> int:
    best_i = 0
    best_d = abs(freqs[0] - target)
    for i in range(1, len(freqs)):
        d = abs(freqs[i] - target)
        if d < best_d or (d == best_d and freqs[i] < freqs[best_i]):
            best_i = i
            best_d = d
    return best_i


def _bin_label(d: float) -> str:
    lo = math.floor(d)
    return f"{lo}~{lo + 1}"


def _bin_range(present: list[float]) -> tuple[int, int]:
    return math.floor(min(present)), math.ceil(max(present))


def _replace_sheet(wb, name: str) -> Worksheet:
    if name in wb.sheetnames:
        del wb[name]
    return wb.create_sheet(name)


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Write freq_bins_<tag> sheets.")
    parser.add_argument("--params", required=True, type=Path)
    args = parser.parse_args(argv)

    params = load_params(args.params)
    xlsx_path = resolve_under_output(params, "process_xlsx", args.params)
    angles = params.get("angles") or []
    axial = params.get("axial_angle") or ""
    f_lo = float(params.get("f_lo_hz") or 0)
    f_hi = float(params.get("f_hi_hz") or 0)
    focus_freqs = [float(v) for v in (params.get("focus_freqs") or [])]

    if not angles:
        print("params.angles is empty", file=sys.stderr)
        return 2

    wb = load_workbook(xlsx_path)
    written: list[str] = []

    for angle in angles:
        if angle == axial:
            continue
        tag = normalize_angle_tag(angle)
        delta_name = f"delta_{tag}"
        if delta_name not in wb.sheetnames:
            print(f"delta sheet {delta_name!r} missing", file=sys.stderr)
            return 2
        freqs, samples, cols = read_angle_sheet(wb[delta_name])

        active_freqs: list[float] = []
        per_freq_deltas: list[list[float]] = []
        per_freq_bins: list[list[tuple[int, int]]] = []
        for ff in focus_freqs:
            idx = _nearest_freq_index(freqs, ff)
            nearest = freqs[idx]
            if nearest < f_lo or nearest > f_hi:
                print(f"focus_freq {ff} -> nearest {nearest} out of band, skip", file=sys.stderr)
                continue
            deltas = [cols[si][idx] for si in range(len(samples))]
            lo, hi = _bin_range(deltas)
            counts: dict[int, int] = {b: 0 for b in range(lo, hi)}
            for d in deltas:
                b = max(lo, min(hi - 1, math.floor(d)))
                counts[b] += 1
            active_freqs.append(ff)
            per_freq_deltas.append(deltas)
            per_freq_bins.append([(b, counts[b]) for b in range(lo, hi)])

        if not active_freqs:
            continue

        detail_name = f"freq_bins_{tag}"
        ws_d = _replace_sheet(wb, detail_name)
        headers = ["样机"]
        for ff in active_freqs:
            hz = _format_hz(ff)
            headers.append(f"{hz}Hz差值")
            headers.append(f"{hz}Hz档位")
        ws_d.append(headers)
        for si, sname in enumerate(samples):
            row = [sname]
            for fi in range(len(active_freqs)):
                d = per_freq_deltas[fi][si]
                row.append(d)
                row.append(_bin_label(d))
            ws_d.append(row)

        summary_name = f"freq_bins_summary_{tag}"
        ws_s = _replace_sheet(wb, summary_name)
        sheaders: list[str] = []
        for ff in active_freqs:
            hz = _format_hz(ff)
            sheaders.append(f"{hz}分组")
            sheaders.append(f"{hz}每组数量")
        ws_s.append(sheaders)
        max_rows = max((len(b) for b in per_freq_bins), default=0)
        for r in range(max_rows):
            row: list = []
            for fi in range(len(active_freqs)):
                bins = per_freq_bins[fi]
                if r < len(bins):
                    lo, count = bins[r]
                    row.append(f"{lo}~{lo + 1}")
                    row.append(count)
                else:
                    row.append(None)
                    row.append(None)
            ws_s.append(row)

        written.append(detail_name)
        written.append(summary_name)

    wb.save(xlsx_path)
    print(f"run_freq_bins: wrote {len(written)} sheets: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd .cursor\skills\fr-curve-directivity-analysis\scripts && python -m pytest tests/test_run_freq_bins.py::test_basic_two_freqs -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "feat(C): add run_freq_bins.py core skeleton with 1dB binning"
```

---

## Task 2: None delta 处理

**Files:**
- Modify: `.cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py`（`_bin_label` + 主循环）
- Test: `tests/test_run_freq_bins.py`（追加 `test_none_delta`）

**Interfaces:**
- Consumes: 同 Task 1
- Produces: 同 Task 1；None delta → 档位 `"N/A"`，统计不计入

- [ ] **Step 1: 追加失败测试**

在 `tests/test_run_freq_bins.py` 末尾追加：

```python
def test_none_delta(tmp_path):
    # S02 has a blank cell at 1000Hz in the angle sheet -> delta None at that freq
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [2.0, None, 6.0]]  # S02 blank at 1000Hz (index 1)
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    ws_d = wb["freq_bins_90"]
    # S01 delta=+1 -> "1~2"; S02 delta=None -> "N/A"
    assert str(ws_d.cell(2, 3).value) == "1~2"
    assert str(ws_d.cell(3, 3).value) == "N/A"
    # summary: only 1 non-None delta -> total count == 1
    ws_s = wb["freq_bins_summary_90"]
    total = 0
    for r in range(2, ws_s.max_row + 1):
        v = ws_s.cell(r, 2).value
        if v is not None:
            total += int(v)
    assert total == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_run_freq_bins.py::test_none_delta -v`
Expected: FAIL（`_bin_label(None)` 调 `math.floor(None)` 抛 TypeError）

- [ ] **Step 3: 改 `_bin_label` 与主循环 None 处理**

把 `run_freq_bins.py` 的 `_bin_label` 改为：

```python
def _bin_label(d: float | None) -> str:
    if d is None:
        return "N/A"
    lo = math.floor(d)
    return f"{lo}~{lo + 1}"
```

把主循环里取 deltas 与计 bin 的两段改为（None 不计入 bin）：

```python
            deltas = [cols[si][idx] for si in range(len(samples))]
            present = [d for d in deltas if d is not None]
            if not present:
                lo, hi = 0, 1
            else:
                lo, hi = _bin_range(present)
            counts: dict[int, int] = {b: 0 for b in range(lo, hi)}
            for d in deltas:
                if d is None:
                    continue
                b = max(lo, min(hi - 1, math.floor(d)))
                counts[b] += 1
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py -v`
Expected: PASS（两个测试都过）

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "feat(C): handle None delta in run_freq_bins (N/A label, excluded from counts)"
```

---

## Task 3: focus_freqs 为空时合法跳过

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_empty_focus_freqs`）

**Interfaces:** 同 Task 1。`focus_freqs=[]` → exit 0，不写 sheet。

- [ ] **Step 1: 追加测试**

```python
def test_empty_focus_freqs(tmp_path):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    assert "freq_bins_90" not in wb.sheetnames
    assert "freq_bins_summary_90" not in wb.sheetnames
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_empty_focus_freqs -v`
Expected: PASS（Task 1 主循环 `for ff in focus_freqs` 不执行 → `active_freqs` 空 → `continue` → 不写 sheet）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify empty focus_freqs skips sheet writing (exit 0)"
```

---

## Task 4: 部分 focus_freq 超分析频段时跳过该频点

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_freq_out_of_band`）

**Interfaces:** 超频段频点 → warning 到 stderr，跳过；其余频点正常出列。

- [ ] **Step 1: 追加测试**

```python
def test_freq_out_of_band(tmp_path, capsys):
    # f_lo=250, f_hi=20000; focus 50Hz is below band
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[50, 1000])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    ws_d = wb["freq_bins_90"]
    # only 1000Hz active -> cols = 1 + 1*2 = 3
    assert ws_d.max_column == 3
    assert "1000Hz" in str(ws_d.cell(1, 2).value)
    # 50Hz column must NOT exist
    for c in range(1, ws_d.max_column + 1):
        assert "50Hz" not in str(ws_d.cell(1, c).value)
    captured = capsys.readouterr()
    assert "out of band" in captured.err
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_freq_out_of_band -v`
Expected: PASS（Task 1 已有 `if nearest < f_lo or nearest > f_hi: skip`）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify out-of-band focus_freq is skipped with warning"
```

---

## Task 5: 全部 focus_freq 超频段 → exit 0 + 无 sheet

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_all_freqs_out_of_band_exit0`）

- [ ] **Step 1: 追加测试**

```python
def test_all_freqs_out_of_band_exit0(tmp_path, capsys):
    # f_lo=250, f_hi=20000; both focus freqs below band
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[50, 80])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    assert "freq_bins_90" not in wb.sheetnames
    captured = capsys.readouterr()
    assert "out of band" in captured.err
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_all_freqs_out_of_band_exit0 -v`
Expected: PASS（所有 ff 跳过 → `active_freqs` 空 → `continue`）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify all focus_freqs out of band exits 0 with warnings"
```

---

## Task 6: 幂等（重跑不重复 sheet）

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_idempotent`）

- [ ] **Step 1: 追加测试**

```python
def test_idempotent(tmp_path):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000])

    run_freq_bins_main(["--params", str(out / "params.json")])
    run_freq_bins_main(["--params", str(out / "params.json")])

    wb = load_workbook(out / "process.xlsx")
    freq_bins_sheets = [n for n in wb.sheetnames if n.startswith("freq_bins")]
    # exactly 2: freq_bins_90 + freq_bins_summary_90, no duplicates
    assert sorted(freq_bins_sheets) == ["freq_bins_90", "freq_bins_summary_90"]
    ws_d = wb["freq_bins_90"]
    assert ws_d.max_row == 1 + 2  # not doubled
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_idempotent -v`
Expected: PASS（`_replace_sheet` 删旧建新）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify run_freq_bins is idempotent (no duplicate sheets)"
```

---

## Task 7: focus_freqs 输入校验（exit 2）

**Files:**
- Modify: `run_freq_bins.py`（加 `_validate_focus_freqs` + 在 main 调用）
- Test: `tests/test_run_freq_bins.py`（追加 `test_invalid_focus_freqs_exit2`）

**Interfaces:** 非法 focus_freqs（非数值/负数/零/重复）→ exit 2，不跑。

- [ ] **Step 1: 追加失败测试**

```python
import json

def test_invalid_focus_freqs_exit2(tmp_path):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000])

    bad_values = [[-1000], [0], ["x"], [1000, 1000]]  # negative, zero, non-numeric, dup
    for bv in bad_values:
        (out / "params.json").write_text(
            json.dumps({
                "product": "T", "note": "", "data_root": str(out), "output_dir": str(out),
                "unit": "dB", "f_lo_hz": 250, "f_hi_hz": 20000,
                "process_xlsx": "process.xlsx", "process_md": "process.md",
                "angles": ["axis", "90"], "axial_angle": "axis", "sample_count": 2,
                "envelope": None, "focus_freqs": bv,
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        rc = run_freq_bins_main(["--params", str(out / "params.json")])
        assert rc == 2, f"expected exit 2 for focus_freqs={bv}"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_run_freq_bins.py::test_invalid_focus_freqs_exit2 -v`
Expected: FAIL（负数/零当前不报错；重复当前不去重；非数值当前 `float("x")` 抛 ValueError 而非 exit 2）

- [ ] **Step 3: 加校验函数 + 在 main 调用**

在 `run_freq_bins.py` 顶部（`_format_hz` 之前）加：

```python
def _validate_focus_freqs(ff: list) -> list[float]:
    if not isinstance(ff, list):
        print("focus_freqs must be a list", file=sys.stderr)
        return None  # type: ignore[return-value]
    seen: set[float] = set()
    out: list[float] = []
    for v in ff:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            print(f"focus_freqs element not numeric: {v!r}", file=sys.stderr)
            return None  # type: ignore[return-value]
        fv = float(v)
        if fv <= 0:
            print(f"focus_freqs must be > 0: {fv}", file=sys.stderr)
            return None  # type: ignore[return-value]
        if fv in seen:
            print(f"focus_freqs duplicate: {fv}", file=sys.stderr)
            return None  # type: ignore[return-value]
        seen.add(fv)
        out.append(fv)
    return out
```

把 main 里读 focus_freqs 的那行改为：

```python
    raw_ff = params.get("focus_freqs")
    if raw_ff is None:
        focus_freqs = []
    else:
        validated = _validate_focus_freqs(raw_ff)
        if validated is None:
            return 2
        focus_freqs = validated
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py -v`
Expected: PASS（全部测试）

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "feat(C): validate focus_freqs (numeric, >0, dedupe) with exit 2 on invalid"
```

---

## Task 8: 缺 delta sheet 时 exit 2

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_missing_delta_sheet_exit2`）

- [ ] **Step 1: 追加测试**

```python
def test_missing_delta_sheet_exit2(tmp_path):
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        extra={"focus_freqs": [1000]},
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
    # do NOT run run_deltas -> no delta_90 sheet

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 2
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_missing_delta_sheet_exit2 -v`
Expected: PASS（Task 1 已有 `if delta_name not in wb.sheetnames: return 2`）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify missing delta sheet exits 2"
```

---

## Task 9: 所有 present delta 同值时 bin 范围不空（纯测试）

**Files:**
- Test: `tests/test_run_freq_bins.py`（追加 `test_identical_deltas`）

**Note:** `_bin_range` 的 `lo==hi → hi=lo+1` 边界修复已在 Task 2 提前应用（Task 2 的 `test_none_delta` 单非None delta 场景需要它）。本任务只补测试验证该行为。

**Interfaces:** `floor(min)==ceil(max)` 时强制 `[v, v+1)`（已实现）。

- [ ] **Step 1: 追加测试**

```python
def test_identical_deltas(tmp_path):
    # all deltas at 1000Hz are exactly +2.0 -> single bin "2~3"
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[3.0, 4.0, 5.0], [3.0, 4.0, 5.0]]  # both +2.0
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0

    wb = load_workbook(out / "process.xlsx")
    ws_d = wb["freq_bins_90"]
    assert str(ws_d.cell(2, 3).value) == "2~3"
    assert str(ws_d.cell(3, 3).value) == "2~3"
    ws_s = wb["freq_bins_summary_90"]
    # exactly one bin row, count == 2
    assert ws_s.max_row == 2
    assert str(ws_s.cell(2, 1).value) == "2~3"
    assert int(ws_s.cell(2, 2).value) == 2
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py::test_identical_deltas -v`
Expected: PASS（`_bin_range` 的 lo==hi 守卫已在 Task 2 应用）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "test(C): verify identical deltas produce non-empty bin range"
```

---

## Task 10: L2 跑后自检（机械验证）

**Files:**
- Modify: `run_freq_bins.py`（加 `_verify_sheets` + 集成到 main：写后→自检→失败删 sheet + exit 3）
- Test: `tests/test_run_freq_bins.py`（追加 `test_verification_pass` + `test_verification_fail_exit3`）

**Interfaces:** 自检失败 → 删刚写的 `freq_bins_*` sheet → exit 3；通过 → stdout 打 `VERIFICATION OK: ...`。

- [ ] **Step 1: 追加失败测试**

```python
def test_verification_pass(tmp_path, capsys):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000, 4000])

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 0
    captured = capsys.readouterr()
    assert "VERIFICATION OK" in captured.out


def test_verification_fail_exit3(tmp_path, monkeypatch):
    axis_cols = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    angle_cols = [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]]
    out = _prep(tmp_path, axis_cols=axis_cols, angle_cols=angle_cols, focus_freqs=[1000])

    # sabotage: make _bin_label produce an invalid label -> verify must catch -> exit 3
    import run_freq_bins
    monkeypatch.setattr(run_freq_bins, "_bin_label", lambda d: "BAD" if d is not None else "N/A")

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 3

    wb = load_workbook(out / "process.xlsx")
    assert "freq_bins_90" not in wb.sheetnames, "bad sheet must be deleted on verify fail"
    assert "freq_bins_summary_90" not in wb.sheetnames


def test_verification_fail_deletes_all_angles(tmp_path, monkeypatch):
    # two non-axial angles; sabotage kicks in on first angle -> both must be absent
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90", "180"],
        axial_angle="axis",
        sample_count=2,
        extra={"focus_freqs": [1000]},
    )
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90", "180"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0],
        values_by_angle={
            "axis": [[1.0, 2.0], [1.0, 2.0]],
            "90": [[2.0, 3.0], [3.0, 4.0]],
            "180": [[0.0, 1.0], [-1.0, 0.0]],
        },
    )
    run_deltas_main(["--params", str(out / "params.json")])

    import run_freq_bins
    monkeypatch.setattr(run_freq_bins, "_bin_label", lambda d: "BAD" if d is not None else "N/A")

    rc = run_freq_bins_main(["--params", str(out / "params.json")])
    assert rc == 3

    wb = load_workbook(out / "process.xlsx")
    for tag in ("90", "180"):
        assert f"freq_bins_{tag}" not in wb.sheetnames
        assert f"freq_bins_summary_{tag}" not in wb.sheetnames
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_run_freq_bins.py::test_verification_pass tests/test_run_freq_bins.py::test_verification_fail_exit3 tests/test_run_freq_bins.py::test_verification_fail_deletes_all_angles -v`
Expected: FAIL（无 `_verify_sheets`，无 VERIFICATION OK 输出；sabotage 后无 exit 3）

- [ ] **Step 3: 加 `_verify_sheets` 函数**

在 `run_freq_bins.py` 顶部 import 后加：

```python
import re

_BIN_LABEL_RE = re.compile(r"^-?\d+~-?\d+$")


def _verify_sheets(
    wb,
    angle: str,
    samples: list[str],
    active_freqs: list[float],
) -> None:
    """Raise ValueError on any check failure. Spec §6.1 checks 1-11."""
    tag = normalize_angle_tag(angle)
    detail_name = f"freq_bins_{tag}"
    summary_name = f"freq_bins_summary_{tag}"

    if detail_name not in wb.sheetnames:
        raise ValueError(f"missing sheet {detail_name}")
    if summary_name not in wb.sheetnames:
        raise ValueError(f"missing sheet {summary_name}")

    ws_d = wb[detail_name]
    expected_d_cols = 1 + 2 * len(active_freqs)
    if ws_d.max_column != expected_d_cols:
        raise ValueError(f"{detail_name} cols {ws_d.max_column} != {expected_d_cols}")
    expected_d_rows = 1 + len(samples)
    if ws_d.max_row != expected_d_rows:
        raise ValueError(f"{detail_name} rows {ws_d.max_row} != {expected_d_rows}")

    for si, sname in enumerate(samples):
        v = ws_d.cell(si + 2, 1).value
        if str(v).strip() != str(sname).strip():
            raise ValueError(f"{detail_name} sample R{si+2} mismatch: {v!r} vs {sname!r}")

    for r in range(2, ws_d.max_row + 1):
        for c in range(3, ws_d.max_column + 1, 2):  # bin columns are odd (3,5,7...)
            v = ws_d.cell(r, c).value
            if v is None:
                continue
            s = str(v).strip()
            if s != "N/A" and not _BIN_LABEL_RE.match(s):
                raise ValueError(f"{detail_name} bad bin label R{r}C{c}: {s!r}")
            if s != "N/A":
                lo_s, hi_s = s.split("~")
                if int(lo_s) + 1 != int(hi_s):
                    raise ValueError(f"{detail_name} bad bin width R{r}C{c}: {s!r}")

    ws_s = wb[summary_name]
    expected_s_cols = 2 * len(active_freqs)
    if ws_s.max_column != expected_s_cols:
        raise ValueError(f"{summary_name} cols {ws_s.max_column} != {expected_s_cols}")
    a1 = ws_s.cell(1, 1).value
    if a1 is None or "分组" not in str(a1):
        raise ValueError(f"{summary_name} A1 must be 分组 title, got {a1!r}")

    for fi in range(len(active_freqs)):
        count_col = 2 + fi * 2  # 1-indexed
        total = 0
        for r in range(2, ws_s.max_row + 1):
            v = ws_s.cell(r, count_col).value
            if v is not None:
                total += int(v)
        non_none = sum(
            1 for si in range(len(samples)) if ws_d.cell(si + 2, 2 + fi * 2).value is not None
        )
        if total != non_none:
            raise ValueError(f"{summary_name} freq#{fi} sum {total} != non-None {non_none}")
```

- [ ] **Step 4: 集成到 main（写后→自检→失败删 sheet + exit 3）**

把 main 里每个角度的写 sheet 段改为（在 `written.append(detail_name)` 之前插自检）：

```python
        # ... (detail sheet 与 summary sheet 写入代码不变) ...

        try:
            _verify_sheets(wb, angle, samples, active_freqs)
        except ValueError as e:
            # delete ALL freq_bins sheets written so far (current + prior angles)
            # to avoid leaving partial output on multi-angle failure
            if detail_name in wb.sheetnames:
                del wb[detail_name]
            if summary_name in wb.sheetnames:
                del wb[summary_name]
            for name in written:
                if name in wb.sheetnames:
                    del wb[name]
            print(f"VERIFICATION FAIL for {angle!r}: {e}", file=sys.stderr)
            wb.save(xlsx_path)
            return 3

        written.append(detail_name)
        written.append(summary_name)
```

把 main 末尾的 print 改为：

```python
    wb.save(xlsx_path)
    n_angles = len(written) // 2
    print(
        f"VERIFICATION OK: {n_angles} angles x 2 sheets, "
        f"{len(samples)} samples, {len(active_freqs)} freq points"
    )
    return 0
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest tests/test_run_freq_bins.py -v`
Expected: PASS（全部 12 个测试）

- [ ] **Step 6: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_run_freq_bins.py
git commit -m "feat(C): add L2 post-run self-check in run_freq_bins (exit 3 + delete bad sheets)"
```

---

## Task 11: compose_html 渲染频点差值分档节

**Files:**
- Modify: `scripts/compose_html.py`（加 `build_freq_bins_html` + 集成到 `compose_report_html`）
- Modify: `scripts/templates/report.html.j2`（在差值节和一致性节之间插新节）
- Create: `scripts/tests/test_compose_freq_bins.py`

**Interfaces:**
- Consumes: `params.json`（`focus_freqs`），`freq_bins_<tag>` + `freq_bins_summary_<tag>` sheet
- Produces: report.html 含"频点差值分档"节；`compose_report_html(...) -> Path`

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
"""Tests for compose_html freq_bins section rendering."""
from __future__ import annotations

from pathlib import Path

from compose_html import compose_report_html
from conftest import build_angle_workbook, write_params
from run_deltas import main as run_deltas_main
from run_freq_bins import main as run_freq_bins_main


def _prep(tmp_path: Path, *, focus_freqs) -> Path:
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
        axial_angle="axis",
        sample_count=2,
        extra={"focus_freqs": focus_freqs},
    )
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0, 4000.0],
        values_by_angle={
            "axis": [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]],
            "90": [[2.0, 3.0, 4.0], [4.0, 5.0, 6.0]],
        },
    )
    run_deltas_main(["--params", str(out / "params.json")])
    run_freq_bins_main(["--params", str(out / "params.json")])
    return out


def test_render_freq_bins_section(tmp_path):
    out = _prep(tmp_path, focus_freqs=[1000, 4000])

    html_path = compose_report_html(out)
    text = html_path.read_text(encoding="utf-8")
    assert "频点差值分档" in text
    assert "freq_bins_90" in text or "90" in text  # angle label appears
    assert "1000Hz" in text
    assert "4000Hz" in text
    # both detail and summary tables rendered
    assert "分组" in text
    assert "每组数量" in text
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd .cursor\skills\fr-curve-directivity-analysis\scripts && python -m pytest tests/test_compose_freq_bins.py::test_render_freq_bins_section -v`
Expected: FAIL（report.html 不含"频点差值分档"节）

- [ ] **Step 3: 加 `build_freq_bins_html` 到 `compose_html.py`**

在 `compose_html.py` 的 `build_consistency_summary_html` 之后加：

```python
def build_freq_bins_html(output_dir: Path, params: dict) -> str:
    """Render freq_bins detail + summary tables per non-axial angle.

    Returns "" if focus_freqs is empty or no freq_bins sheets exist.
    Raises SystemExit(2) if focus_freqs non-empty but a required sheet is missing.
    """
    focus_freqs = params.get("focus_freqs") or []
    if not focus_freqs:
        return ""
    angles = params.get("angles") or []
    axial = params.get("axial_angle") or ""
    xlsx_path = output_dir / "process.xlsx"
    if not xlsx_path.is_file():
        return ""
    wb = load_workbook(xlsx_path)

    body = '<h2>频点差值分档</h2>'
    for angle in angles:
        if angle == axial:
            continue
        tag = normalize_angle_tag(angle)
        detail_name = f"freq_bins_{tag}"
        summary_name = f"freq_bins_summary_{tag}"
        if detail_name not in wb.sheetnames:
            raise SystemExit(2)
        if summary_name not in wb.sheetnames:
            raise SystemExit(2)
        body += f'<h3>角度 {html.escape(str(angle))}</h3>'

        # detail table
        ws_d = wb[detail_name]
        body += '<table class="freq-bins-detail"><thead><tr>'
        for c in range(1, ws_d.max_column + 1):
            h = ws_d.cell(1, c).value
            body += f"<th>{html.escape(str(h or ''))}</th>"
        body += "</tr></thead><tbody>"
        for r in range(2, ws_d.max_row + 1):
            body += "<tr>"
            for c in range(1, ws_d.max_column + 1):
                v = ws_d.cell(r, c).value
                body += f"<td>{html.escape(str(v if v is not None else ''))}</td>"
            body += "</tr>"
        body += "</tbody></table>"

        # summary table
        ws_s = wb[summary_name]
        body += '<table class="freq-bins-summary"><thead><tr>'
        for c in range(1, ws_s.max_column + 1):
            h = ws_s.cell(1, c).value
            body += f"<th>{html.escape(str(h or ''))}</th>"
        body += "</tr></thead><tbody>"
        for r in range(2, ws_s.max_row + 1):
            if all(ws_s.cell(r, c).value is None for c in range(1, ws_s.max_column + 1)):
                continue
            body += "<tr>"
            for c in range(1, ws_s.max_column + 1):
                v = ws_s.cell(r, c).value
                body += f"<td>{html.escape(str(v if v is not None else ''))}</td>"
            body += "</tr>"
        body += "</tbody></table>"
    return body
```

- [ ] **Step 4: 集成到 `compose_report_html` + 模板**

在 `compose_report_html` 里，`consistency_summary_html = ...` 行之前加：

```python
    freq_bins_html = build_freq_bins_html(output_dir, params)
```

并在 `tpl.render(...)` 调用里加参数：

```python
        freq_bins_html=freq_bins_html,
```

改 `scripts/templates/report.html.j2`，把现有 4 个 section 重编号为 1-5（在差值节和一致性节之间插新节）。完整新模板：

```jinja
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{{ product }} — 指向性分析报告</title>
  <style>{{ css }}</style>
</head>
<body>
  <h1>{{ product }} 指向性分析报告</h1>

  <section class="section section-keep" id="intro">
    <h2>1. 整体介绍</h2>
    {{ intro_html | safe }}
  </section>

  <section class="section section-flow" id="deltas">
    <h2>2. 差值分析</h2>
    {% if deltas_notes_html %}
    {{ deltas_notes_html | safe }}
    {% endif %}
    <div class="figures">
      {% for fig in delta_figures %}
      <div class="figure">
        <img src="{{ fig.src }}" alt="{{ fig.caption }}" />
        <div class="caption">{{ fig.caption }}</div>
      </div>
      {% endfor %}
    </div>
  </section>

  {% if freq_bins_html %}
  <section class="section section-keep" id="freq-bins">
    <h2>3. 频点差值分档</h2>
    {{ freq_bins_html | safe }}
  </section>
  {% endif %}

  <section class="section section-keep" id="consistency">
    <h2>4. 一致性分析</h2>
    {% if consistency_notes_html %}
    {{ consistency_notes_html | safe }}
    {% endif %}
    {{ consistency_summary_html | safe }}
    <div class="figures">
      {% for fig in consistency_figures %}
      <div class="figure">
        <img src="{{ fig.src }}" alt="{{ fig.caption }}" />
        <div class="caption">{{ fig.caption }}</div>
      </div>
      {% endfor %}
    </div>
  </section>

  <section class="section section-keep" id="conclusion">
    <h2>5. 结论</h2>
    {{ conclusion_html | safe }}
  </section>
</body>
</html>
```

注意：`freq_bins_html` 已含 `<h2>3. 频点差值分档</h2>`（在 `build_freq_bins_html` 里），所以模板里用 `<h2>3. 频点差值分档</h2>` 会重复。需把 `build_freq_bins_html` 里的开头 `<h2>频点差值分档</h2>` 去掉，改由模板提供标题。

把 `build_freq_bins_html` 里的 `body = '<h2>频点差值分档</h2>'` 改为 `body = ''`。

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest tests/test_compose_freq_bins.py::test_render_freq_bins_section -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/compose_html.py .cursor/skills/fr-curve-directivity-analysis/scripts/templates/report.html.j2 .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_freq_bins.py
git commit -m "feat(C): render freq-bins section in directivity report (detail + summary tables)"
```

---

## Task 12: focus_freqs 为空时跳过频点节

**Files:**
- Test: `tests/test_compose_freq_bins.py`（追加 `test_skip_when_empty`）

- [ ] **Step 1: 追加测试**

```python
def test_skip_when_empty(tmp_path):
    out = _prep(tmp_path, focus_freqs=[])

    html_path = compose_report_html(out)
    text = html_path.read_text(encoding="utf-8")
    assert "频点差值分档" not in text
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_compose_freq_bins.py::test_skip_when_empty -v`
Expected: PASS（`build_freq_bins_html` 在 `focus_freqs=[]` 时返回 `""`，模板 `{% if freq_bins_html %}` 跳过）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_freq_bins.py
git commit -m "test(C): verify freq-bins section skipped when focus_freqs empty"
```

---

## Task 13: focus_freqs 非空但 sheet 缺失 → exit 2

**Files:**
- Test: `tests/test_compose_freq_bins.py`（追加 `test_exit2_when_sheet_missing`）

**Interfaces:** 强制 askuser 机制：focus_freqs 非空但 `freq_bins_*` sheet 不存在 → `SystemExit(2)`，不跳过。

- [ ] **Step 1: 追加测试**

```python
import pytest

def test_exit2_when_sheet_missing(tmp_path):
    out = _prep(tmp_path, focus_freqs=[1000])
    # delete the freq_bins sheets to simulate run_freq_bins not having run / failed
    from openpyxl import load_workbook
    wb = load_workbook(out / "process.xlsx")
    del wb["freq_bins_90"]
    del wb["freq_bins_summary_90"]
    wb.save(out / "process.xlsx")

    with pytest.raises(SystemExit) as exc:
        compose_report_html(out)
    assert exc.value.code == 2
```

- [ ] **Step 2: 跑测试确认通过**

Run: `python -m pytest tests/test_compose_freq_bins.py::test_exit2_when_sheet_missing -v`
Expected: PASS（`build_freq_bins_html` 在 sheet 缺失时 `raise SystemExit(2)`）

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_freq_bins.py
git commit -m "test(C): verify compose_html exits 2 when focus_freqs set but freq_bins sheets missing"
```

---

## Task 14: L3 报告自检（compose_html 写后读回）

**Files:**
- Modify: `compose_html.py`（加 `_verify_report_html` + 集成到 `compose_report_html`：写后→自检→失败 exit 3）
- Test: `tests/test_compose_freq_bins.py`（追加 `test_report_verification_fail_exit3`）

**Interfaces:** focus_freqs 非空时，写完 report.html 后读回验证：含节标题、每角度 2 表、列数正确。失败 → `SystemExit(3)`。

- [ ] **Step 1: 追加失败测试**

```python
def test_report_verification_fail_exit3(tmp_path, monkeypatch):
    out = _prep(tmp_path, focus_freqs=[1000])
    # sabotage: make build_freq_bins_html produce a section missing the summary table
    import compose_html
    orig = compose_html.build_freq_bins_html
    def bad(output_dir, params):
        html = orig(output_dir, params)
        # drop the summary table marker to force L3 check fail
        return html.replace("每组数量", "X")
    monkeypatch.setattr(compose_html, "build_freq_bins_html", bad)

    with pytest.raises(SystemExit) as exc:
        compose_report_html(out)
    assert exc.value.code == 3
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_compose_freq_bins.py::test_report_verification_fail_exit3 -v`
Expected: FAIL（无 `_verify_report_html`，compose 正常返回而非 exit 3）

- [ ] **Step 3: 加 `_verify_report_html` + 集成**

在 `compose_html.py` 加（在 `build_freq_bins_html` 之后）：

```python
import re as _re

def _verify_report_html(
    html_path: Path, params: dict
) -> None:
    """Spec §6.2 L3 checks. Raise ValueError on failure."""
    focus_freqs = params.get("focus_freqs") or []
    if not focus_freqs:
        return  # nothing to verify
    text = html_path.read_text(encoding="utf-8")
    if "频点差值分档" not in text:
        raise ValueError("missing 频点差值分档 section title")
    angles = params.get("angles") or []
    axial = params.get("axial_angle") or ""
    non_axial = [a for a in angles if a != axial]
    if not non_axial:
        return

    # count detail tables (class freq-bins-detail) and summary tables (class freq-bins-summary)
    n_detail = len(_re.findall(r'class="freq-bins-detail"', text))
    n_summary = len(_re.findall(r'class="freq-bins-summary"', text))
    if n_detail != len(non_axial):
        raise ValueError(f"detail tables {n_detail} != non-axial angles {len(non_axial)}")
    if n_summary != len(non_axial):
        raise ValueError(f"summary tables {n_summary} != non-axial angles {len(non_axial)}")
    if "每组数量" not in text:
        raise ValueError("missing 每组数量 header in summary table")

    # column count: count <th> in first detail table header and first summary table header
    expected_d_cols = 1 + 2 * len(focus_freqs)
    expected_s_cols = 2 * len(focus_freqs)

    # extract first detail table thead <tr>...</tr>
    m = _re.search(r'class="freq-bins-detail"><thead><tr>(.*?)</tr>', text)
    if not m:
        raise ValueError("cannot parse detail table header")
    d_th_count = len(_re.findall(r"<th>", m.group(1)))
    if d_th_count != expected_d_cols:
        raise ValueError(f"detail table cols {d_th_count} != {expected_d_cols}")

    m = _re.search(r'class="freq-bins-summary"><thead><tr>(.*?)</tr>', text)
    if not m:
        raise ValueError("cannot parse summary table header")
    s_th_count = len(_re.findall(r"<th>", m.group(1)))
    if s_th_count != expected_s_cols:
        raise ValueError(f"summary table cols {s_th_count} != {expected_s_cols}")
```

把 `compose_report_html` 末尾（`write_text(out, rendered)` 之后）加：

```python
    try:
        _verify_report_html(out, params)
    except ValueError as e:
        print(f"REPORT VERIFICATION FAIL: {e}", file=sys.stderr)
        raise SystemExit(3)
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_compose_freq_bins.py -v`
Expected: PASS（全部 4 个测试）

- [ ] **Step 5: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/scripts/compose_html.py .cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_freq_bins.py
git commit -m "feat(C): add L3 report self-check in compose_html (exit 3 on verify fail)"
```

---

## Task 15: SKILL.md SOP 改动（intake 加问 + 步骤3b + 报告节）

**Files:**
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md`

**Interfaces:** 无代码接口；改 SOP 文档让 Agent 知道何时问 focus_freqs、何时跑 run_freq_bins、报告含频点节。

- [ ] **Step 1: 改 intake 步骤（步骤0）**

在 `SKILL.md` 的「步骤 0：Intake → 先收信息」表后，C 专有项表里加一行：

```markdown
| 关注频点 | 默认 `[1000]`；主动问"默认关注 1000Hz 差值，要不要加其他频点？" → 写入 `params.focus_freqs` |
```

- [ ] **Step 2: 改步骤3（加 3.2 频点分档，原 3.2 顺移为 3.3）**

把 `SKILL.md` 步骤3 的「执行顺序：3.1 → 3.2」改为「执行顺序：3.1 → 3.2 → 3.3」。

在「### 3.1 差值」节之后、「### 3.2 一致性」节之前，插入新节：

```markdown
### 3.2 频点分档

跑

\`\`\`text
python .cursor/skills/fr-curve-directivity-analysis/scripts/run_freq_bins.py --params <产出目录>/params.json
\`\`\`

脚本读 `delta_<tag>` sheet，对 `params.focus_freqs` 每个频点找最近频率，按 1dB 一档统计各角度差值分布，写出 `freq_bins_<tag>`（明细）与 `freq_bins_summary_<tag>`（统计）两张 sheet/角度。跑后自检失败 → 删坏 sheet + exit 3。

`focus_freqs=[]` → 合法跳过，不写 sheet。`focus_freqs` 非空但 `delta_*` sheet 缺失 → exit 2。
```

把原「### 3.2 一致性」标题改为「### 3.3 一致性」。

把「### 3.3 聊天短结（必做）」标题改为「### 3.4 聊天短结（必做）」。

把硬规则 1「必须按 3.1 → 3.2 → 3.3」改为「必须按 3.1 → 3.2 → 3.3 → 3.4」。

- [ ] **Step 3: 改步骤4（报告节说明）**

在「### 4.2 准备四段白话文本参数」之后、「### 4.3 组 HTML」之前，加一句：

```markdown
频点差值分档节由 `compose_html.py` 从 `freq_bins_*` sheet 自动渲染（focus_freqs 非空时）；Agent 无需手写该节内容。
```

- [ ] **Step 4: 改铁律**

把铁律 1 末尾的「`delta_*` / `consistency_*`」改为「`delta_*` / `freq_bins_*` / `consistency_*`」。

把交付物表里 `process.xlsx` 行的「步骤3脚本追加 `delta_*` / `consistency_*`」改为「步骤3脚本追加 `delta_*` / `freq_bins_*` / `consistency_*`」。

- [ ] **Step 5: 验证文档可读**

Run: 打开 `SKILL.md`，目检步骤3 有 3.1/3.2/3.3/3.4 四个子节，intake 表有"关注频点"行。
Expected: 结构完整，无断号。

- [ ] **Step 6: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/SKILL.md
git commit -m "docs(C): add focus_freqs intake + step 3b run_freq_bins + report section to SOP"
```

---

## Task 16: references 文件改动

**Files:**
- Modify: `references/params.template.json`
- Modify: `references/data-contract-sheets.md`
- Modify: `references/report-outline.md`
- Modify: `references/fill-chat-summary.md`

**Interfaces:** 无代码接口；数据合同/模板/大纲/短结同步频点分档。

- [ ] **Step 1: `params.template.json` 加 `focus_freqs`**

把 `references/params.template.json` 改为：

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
  "envelope": null,
  "focus_freqs": [1000]
}
```

- [ ] **Step 2: `data-contract-sheets.md` 加两节**

在 `data-contract-sheets.md` 的「## `consistency_<tag>`」节之前，插入：

```markdown
## `freq_bins_<tag>`（步骤3，`run_freq_bins.py` 写）

每个非轴向角度一张。明细表：每行一个样机，列 = 样机 + 每个关注频点 ×（差值, 档位）。

| 位置 | 内容 |
|------|------|
| A 列 | 样机名 |
| 第 1 行 B 列起 | 交替列头：`<freq>Hz差值` / `<freq>Hz档位` |
| B2 起 | 该样机在该频点的差值（float 或空）与档位（`"lo~hi"` 1dB 左闭右开，或 `N/A`） |

档位规则：`floor(d)~floor(d)+1`；差值为 None → 档位 `N/A`。
`focus_freqs=[]` 时不生成任何 `freq_bins_*` sheet。

## `freq_bins_summary_<tag>`（步骤3，`run_freq_bins.py` 写）

每个非轴向角度一张。统计表，**无左表头**（A1 = 第一个频点的"分组"标题）。

| 位置 | 内容 |
|------|------|
| 第 1 行 | 交替列头：`<freq>分组` / `<freq>每组数量` |
| A2 起 | 该频点各 bin 的下界标签 `"lo~hi"` |
| B2 起 | 该 bin 的样机计数 |

各频点独立分档（`floor(min) ~ ceil(max)` 跨样机）；bin 数不同时短列下方留空。
每频点"每组数量"列求和 == 该频点非 None delta 数。
```

- [ ] **Step 3: `report-outline.md` 加频点节大纲 + 自检项**

在 `report-outline.md` 的「## 章节顺序（固定）」列表里，第 2 项之后、第 3 项之前插：

```markdown
3. **频点差值分档**：脚本从 `freq_bins_<tag>` / `freq_bins_summary_<tag>` sheet 渲染明细表 + 统计表（每非轴向角度各两张）；`focus_freqs=[]` 时整节跳过。Agent 无需手写该节。
```

把原第 3、4 项序号顺移为 4、5。

在「## 自检」表里加两行：

```markdown
| H. 频点差值分档节 | `focus_freqs` 非空时含"频点差值分档"节标题 + 每角度明细表 + 统计表 |
| I. 频点节列数 | 明细表列数 == 1 + 2×len(focus_freqs)；统计表列数 == 2×len(focus_freqs) |
```

- [ ] **Step 4: `fill-chat-summary.md` 加 focus_freqs intake 填法**

在 `fill-chat-summary.md` 顶部说明后加一节：

```markdown
## 步骤0 intake：关注频点填法

默认 `focus_freqs=[1000]`。主动问用户："默认关注 1000Hz 差值，要不要加其他频点？"

- 用户给 `[1000, 4000]` → `params.focus_freqs` 写 `[1000, 4000]`
- 用户说"就 1000" → 写 `[1000]`
- 用户说"不关注" → 写 `[]`（合法跳过，报告无频点节）
```

- [ ] **Step 5: 验证 JSON 合法**

Run: `python -c "import json; json.load(open('.cursor/skills/fr-curve-directivity-analysis/references/params.template.json', encoding='utf-8')); print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/references/params.template.json .cursor/skills/fr-curve-directivity-analysis/references/data-contract-sheets.md .cursor/skills/fr-curve-directivity-analysis/references/report-outline.md .cursor/skills/fr-curve-directivity-analysis/references/fill-chat-summary.md
git commit -m "docs(C): sync references for freq-bins (params template, sheet contract, report outline, chat summary)"
```

---

## 计划自审

**1. 规格覆盖**（对照 spec §9.2 验收标准 12 条）：

| 验收项 | 覆盖任务 |
|--------|----------|
| 1. `[1000]` 出 2 sheet/角度，列数正确 | Task 1（test_basic_two_freqs 用 2 freqs 验） |
| 2. `[1000,4000]` 列数 = 1+2×2 / 2×2 | Task 1 + Task 11 |
| 3. `[]` 无 sheet、无报告节、exit 0 | Task 3 + Task 12 |
| 4. None delta → "N/A"，统计求和 == 非 None 数 | Task 2 |
| 5. 同值 delta → bin `[v,v+1)` | Task 9 |
| 6. 非法 focus_freqs → exit 2 | Task 7 |
| 7. 全部超频段 → exit 0 + warning | Task 5 |
| 8. 部分超频段 → 跳过 + warning | Task 4 |
| 9. L2 自检失败 → exit 3 + sheet 删 | Task 10 |
| 10. L3 自检失败 → exit 3 | Task 14 |
| 11. compose_html focus_freqs 非空但 sheet 缺 → exit 2 | Task 13 |
| 12. 所有 L1 测试通过 | Task 1-14 全部 |

**2. 占位扫描**：无 TBD/TODO/"add appropriate"等；每步含完整代码或完整命令。

**3. 类型一致性**：
- `main(argv) -> int` 在 run_freq_bins 全程一致
- `_bin_label(d: float | None) -> str` 在 Task 1 定义、Task 2 扩 None、Task 10 monkeypatch 用同签名
- `build_freq_bins_html(output_dir, params) -> str` 在 Task 11 定义、Task 14 monkeypatch 用同签名
- `compose_report_html(...) -> Path` 不变
- sheet 名 `freq_bins_<tag>` / `freq_bins_summary_<tag>` 在所有任务一致

**4. 范围纪律**：A/B/shared 不动；C 现有脚本不动；只新增 run_freq_bins + 改 compose_html + 改模板/文档。

---

## 执行交接

计划已保存到 `docs/superpowers/plans/2026-07-19-sp1-freq-bins.md`。两种执行方式：

**1. Subagent-Driven（推荐）** — 每个 Task 派一个新 subagent，任务间 review，快速迭代。

**2. Inline Execution** — 在本会话内按 executing-plans 批量执行，带 checkpoint。

选哪种？










