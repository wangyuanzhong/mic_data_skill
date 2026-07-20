# -*- coding: utf-8 -*-
"""Pytest fixtures for directivity skill scripts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def build_angle_workbook(
    xlsx_path: Path,
    *,
    angles: list[str],
    samples: list[str],
    freqs: list[float],
    values_by_angle: dict[str, list[list[float]]],
) -> None:
    """Build a process.xlsx with one sheet per angle.

    values_by_angle[angle] is columns[sample][freq] (same orientation as
    read_angle_sheet returns).
    """
    wb = Workbook()
    # remove default sheet
    default = wb.active
    wb.remove(default)
    for angle in angles:
        ws = wb.create_sheet(angle)
        ws.append(["freq_hz", *samples])
        cols = values_by_angle[angle]
        for r, f in enumerate(freqs):
            row = [f]
            for i in range(len(samples)):
                row.append(cols[i][r])
            ws.append(row)
    wb.save(xlsx_path)


def write_params(
    params_path: Path,
    *,
    output_dir: Path,
    angles: list[str],
    axial_angle: str,
    sample_count: int,
    f_lo_hz: float = 250.0,
    f_hi_hz: float = 20000.0,
    extra: dict | None = None,
) -> dict:
    data = {
        "product": "TEST",
        "note": "无",
        "data_root": str(output_dir.parent),
        "output_dir": str(output_dir),
        "unit": "dB",
        "f_lo_hz": f_lo_hz,
        "f_hi_hz": f_hi_hz,
        "process_xlsx": "process.xlsx",
        "process_md": "process.md",
        "angles": angles,
        "axial_angle": axial_angle,
        "sample_count": sample_count,
    }
    if extra:
        data.update(extra)
    params_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
