# -*- coding: utf-8 -*-
"""Synthetic curves-sheet + process.md fixtures for golden-analysis skill tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def build_curves_workbook(
    xlsx_path: Path,
    *,
    samples: list[str],
    freqs: list[float],
    values_by_sample: dict[str, list[float | None]],
) -> None:
    """Write a `curves` wide sheet: A=freq_hz, row1 B.. = sample names."""
    wb = Workbook()
    ws = wb.active
    ws.title = "curves"
    ws.append(["freq_hz", *samples])
    for r, f in enumerate(freqs):
        ws.append([f, *[values_by_sample[s][r] for s in samples]])
    wb.save(xlsx_path)


PROCESS_MD_SKELETON = """# 过程记录 · 测试产品 · 无

- 数据根目录：/tmp/fake_root
- 输出目录：../测试产品_20260101_000000/
- 幅度单位：dB
- 曲线分析频段：100–15000 Hz
- 参数文件：params.json（脚本传参；本 md 仅日志）

## 探查结论
### 映射摘要表
### 预览

## 标准化与脚本入参

## 灵敏度分析

## 奇异值分析

## 曲线分析

## 运行说明
"""


def write_process_md(md_path: Path) -> None:
    md_path.write_text(PROCESS_MD_SKELETON, encoding="utf-8")


def write_params(
    params_path: Path,
    *,
    output_dir: Path,
    unit: str = "dB",
    f_lo_hz: float = 100.0,
    f_hi_hz: float = 15000.0,
    sensitivity: dict | None = None,
    curves: dict | None = None,
) -> None:
    data = {
        "product": "测试产品",
        "note": "无",
        "data_root": "/tmp/fake_root",
        "output_dir": str(output_dir),
        "unit": unit,
        "f_lo_hz": f_lo_hz,
        "f_hi_hz": f_hi_hz,
        "process_xlsx": "process.xlsx",
        "process_md": "process.md",
        "sensitivity": sensitivity or {"midline_mode": "mean", "midline_db": None},
        "curves": curves or {"aux_count": 3, "exclude": None, "q_threshold": 10},
    }
    params_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
