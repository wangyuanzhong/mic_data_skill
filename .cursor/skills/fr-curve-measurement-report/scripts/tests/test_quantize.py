# -*- coding: utf-8 -*-
"""Tests for report-side quantize + xlsx_io 1-dp reads."""
from __future__ import annotations

from openpyxl import Workbook

from quantize import q1
from xlsx_io import read_table_dicts, read_wide_curves


def test_q1():
    assert q1(78.285185) == 78.3
    assert q1(None) is None


def test_read_wide_curves_quantizes():
    wb = Workbook()
    ws = wb.active
    ws.append(["freq_hz", "s1"])
    ws.append([100.12, 1.234])
    freqs, samples, cols = read_wide_curves(ws)
    assert freqs == [100.1]
    assert samples == ["s1"]
    assert cols[0] == [1.2]


def test_read_table_dicts_quantizes_numbers():
    wb = Workbook()
    ws = wb.active
    ws.append(["sample", "level_1000", "note"])
    ws.append(["a", 78.285185185, "exact"])
    rows = read_table_dicts(ws)
    assert rows[0]["level_1000"] == 78.3
    assert rows[0]["note"] == "exact"
