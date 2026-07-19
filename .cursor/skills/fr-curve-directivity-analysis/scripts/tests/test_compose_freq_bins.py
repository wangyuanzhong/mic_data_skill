# -*- coding: utf-8 -*-
"""Tests for compose_html freq_bins section rendering."""
from __future__ import annotations

from pathlib import Path

import pytest

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


def test_skip_when_empty(tmp_path):
    out = _prep(tmp_path, focus_freqs=[])

    html_path = compose_report_html(out)
    text = html_path.read_text(encoding="utf-8")
    assert "频点差值分档" not in text


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


def test_report_verification_fail_exit3(tmp_path, monkeypatch):
    out = _prep(tmp_path, focus_freqs=[1000])
    import compose_html
    orig = compose_html.build_freq_bins_html
    def bad(output_dir, params):
        html = orig(output_dir, params)
        return html.replace("每组数量", "X")
    monkeypatch.setattr(compose_html, "build_freq_bins_html", bad)

    with pytest.raises(SystemExit) as exc:
        compose_report_html(out)
    assert exc.value.code == 3
