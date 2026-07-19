# -*- coding: utf-8 -*-
"""Smoke test: render figures + compose report.html on a synthetic batch."""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from compose_html import compose_report_html
from conftest import build_angle_workbook, write_params
from render_figures import main as render_figures_main
from run_cluster import main as run_cluster_main
from run_consistency import main as run_consistency_main
from run_deltas import main as run_deltas_main
from run_peaks import main as run_peaks_main


def _prep_batch(tmp_path: Path) -> Path:
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90", "180"],
        axial_angle="axis",
        sample_count=2,
        extra={
            "cluster_k_max": 5,
            "peak_prominence_db": 0.5,
            "peak_min_octave": 0.1,
            "peak_include_q": True,
        },
    )
    build_angle_workbook(
        out / "process.xlsx",
        angles=["axis", "90", "180"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0, 10000.0],
        values_by_angle={
            "axis": [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]],          # S01, S02
            "90": [[2.0, 3.0, 4.0], [2.5, 3.5, 4.5]],            # +1 / +1.5
            "180": [[0.0, 1.0, 2.0], [-1.0, 0.0, 1.0]],          # -1 / -1
        },
    )
    return out


def _run_analysis(out: Path) -> None:
    assert run_deltas_main(["--params", str(out / "params.json")]) == 0
    assert run_consistency_main(["--params", str(out / "params.json")]) == 0
    assert run_cluster_main(["--params", str(out / "params.json")]) == 0
    assert run_peaks_main(["--params", str(out / "params.json")]) == 0
    assert render_figures_main(["--params", str(out / "params.json")]) == 0


def test_full_pipeline_produces_report_html(tmp_path):
    out = _prep_batch(tmp_path)

    _run_analysis(out)

    figures_dir = out / "figures"
    assert figures_dir.is_dir()
    assert any(figures_dir.glob("差值叠图_*.png")), "no delta figures generated"
    assert (figures_dir / "一致性sigma.png").is_file(), "no consistency sigma figure"

    html_path = compose_report_html(
        out,
        intro_note="测试批次",
        deltas_note="90 度差值较 180 度大",
        consistency_note="180 度散度略高",
        conclusion_note="总体一致性可接受",
    )
    assert html_path.is_file()

    text = html_path.read_text(encoding="utf-8")
    assert "指向性分析报告" in text
    assert "差值分析" in text
    assert "一致性分析" in text
    assert "走势分析" in text
    assert "差值叠图_90" in text
    assert "差值叠图_180" in text
    assert "一致性sigma" in text
    # intro table fields
    assert "分析频段" in text
    assert "轴向参考" in text
    # consistency summary table headers
    assert "max_std_db" in text
    # notes persisted
    assert (out / "report_sections" / "intro_note.txt").is_file()
    assert (out / "report_sections" / "conclusion_note.txt").is_file()


def test_compose_with_empty_notes(tmp_path):
    out = _prep_batch(tmp_path)
    _run_analysis(out)

    html_path = compose_report_html(out)
    assert html_path.is_file()
    text = html_path.read_text(encoding="utf-8")
    assert "差值分析" in text


def test_report_has_no_axial_curve_figure(tmp_path):
    out = _prep_batch(tmp_path)
    _run_analysis(out)

    figures_dir = out / "figures"
    # No figure should be named with axial/axis as a curve plot
    names = [p.name for p in figures_dir.iterdir()]
    assert not any("轴向" in n or n.startswith("axis") for n in names), names
