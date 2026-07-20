# -*- coding: utf-8 -*-
"""--*-note-file CLI args must match B's Windows-safe file-based note pattern."""
from __future__ import annotations

import sys
from pathlib import Path

from conftest import build_angle_workbook, write_params

import compose_html
from run_cluster import main as run_cluster_main
from run_consistency import main as run_consistency_main
from run_deltas import main as run_deltas_main
from run_peaks import main as run_peaks_main


def _prep_batch(tmp_path: Path) -> Path:
    out = tmp_path
    write_params(
        out / "params.json",
        output_dir=out,
        angles=["axis", "90"],
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
        angles=["axis", "90"],
        samples=["S01", "S02"],
        freqs=[100.0, 1000.0, 10000.0],
        values_by_angle={
            "axis": [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]],
            "90": [[2.0, 3.0, 4.0], [2.5, 3.5, 4.5]],
        },
    )
    assert run_deltas_main(["--params", str(out / "params.json")]) == 0
    assert run_consistency_main(["--params", str(out / "params.json")]) == 0
    assert run_cluster_main(["--params", str(out / "params.json")]) == 0
    assert run_peaks_main(["--params", str(out / "params.json")]) == 0
    return out


def test_note_file_args_match_inline_args(tmp_path, monkeypatch):
    """--intro-note-file "<path>" must produce identical report_sections content
    as --intro-note "<same text>" (mirrors report skill's --*-note-file pattern)."""
    out = _prep_batch(tmp_path)

    notes = {
        "intro": "轴向 0 度，90 度离轴一批测试数据",
        "deltas": "90 度差值偏大",
        "consistency": "一致性尚可",
        "trend": "无明显峰谷",
        "conclusion": "结论：符合预期",
    }
    note_files = {}
    for key, text in notes.items():
        p = tmp_path / f"{key}.txt"
        p.write_text(text, encoding="utf-8")
        note_files[key] = p

    # Run 1: inline args (existing behavior, baseline)
    argv_inline = [
        "compose_html.py",
        "--output-dir",
        str(out),
        "--intro-note",
        notes["intro"],
        "--deltas-note",
        notes["deltas"],
        "--consistency-note",
        notes["consistency"],
        "--trend-note",
        notes["trend"],
        "--conclusion-note",
        notes["conclusion"],
    ]
    monkeypatch.setattr(sys, "argv", argv_inline)
    compose_html.main()
    inline_sections = {
        key: (out / "report_sections" / f"{key}_note.txt").read_text(encoding="utf-8").strip()
        for key in notes
    }

    # Run 2: file args (new behavior under test)
    argv_file = [
        "compose_html.py",
        "--output-dir",
        str(out),
        "--intro-note-file",
        str(note_files["intro"]),
        "--deltas-note-file",
        str(note_files["deltas"]),
        "--consistency-note-file",
        str(note_files["consistency"]),
        "--trend-note-file",
        str(note_files["trend"]),
        "--conclusion-note-file",
        str(note_files["conclusion"]),
    ]
    monkeypatch.setattr(sys, "argv", argv_file)
    compose_html.main()
    file_sections = {
        key: (out / "report_sections" / f"{key}_note.txt").read_text(encoding="utf-8").strip()
        for key in notes
    }

    assert file_sections == inline_sections
    for key, text in notes.items():
        assert file_sections[key] == text


def test_note_file_takes_priority_over_inline_when_both_given(tmp_path, monkeypatch):
    out = _prep_batch(tmp_path)
    file_text = "文件里的正文"
    p = tmp_path / "intro.txt"
    p.write_text(file_text, encoding="utf-8")

    argv = [
        "compose_html.py",
        "--output-dir",
        str(out),
        "--intro-note",
        "命令行里的正文（应被忽略）",
        "--intro-note-file",
        str(p),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    compose_html.main()
    got = (out / "report_sections" / "intro_note.txt").read_text(encoding="utf-8").strip()
    assert got == file_text
