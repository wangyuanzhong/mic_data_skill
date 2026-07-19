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
