# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from compose_html import (
    compose_report_html,
    list_figures_in_report_order,
    load_section_html,
)


def test_figure_order_with_bins(tmp_path: Path):
    d = tmp_path / "figures"
    d.mkdir()
    for name in [
        "批量一致性sigma.png",
        "包络分档_正负1.0dB.png",
        "奇异值与剔异前均值.png",
        "归零叠图.png",
        "包络分档_正负0.5dB.png",
        "金标绝对与偏差.png",
    ]:
        (d / name).write_bytes(b"")
    ordered = [p.name for p in list_figures_in_report_order(d)]
    assert ordered[0] == "奇异值与剔异前均值.png"
    assert ordered[1] == "归零叠图.png"
    assert ordered[2] == "包络分档_正负0.5dB.png"
    assert ordered[3] == "包络分档_正负1.0dB.png"
    assert ordered[4] == "金标绝对与偏差.png"
    assert ordered[-1] == "批量一致性sigma.png"


def test_compose_writes_html(synthetic_ready_dir: Path, tmp_path: Path):
    fig_dir = synthetic_ready_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    for name in [
        "奇异值与剔异前均值.png",
        "归零叠图.png",
        "包络分档_正负0.5dB.png",
        "金标绝对与偏差.png",
        "批量一致性sigma.png",
    ]:
        (fig_dir / name).write_bytes(b"x")
    (fig_dir / "批量一致性说明.txt").write_text("一致性说明一行\n", encoding="utf-8")
    html_path = compose_report_html(
        synthetic_ready_dir,
        intro_html="<p>介绍</p>",
        sensitivity_html="<table><tr><td>灵敏度</td></tr></table>",
        curves_notes_html="",
        conclusion_html="<p>结论</p>",
    )
    text = html_path.read_text(encoding="utf-8")
    assert "介绍" in text
    assert "奇异值与剔异前均值.png" in text
    assert "TEST-MIC" in text
    assert "灵敏度分档计数" in text
    assert "幅度范围" in text
    assert "一致性说明一行" in text


def test_load_section_html_prefers_file(tmp_path: Path):
    f = tmp_path / "intro.html"
    f.write_text("<p>from-file</p>", encoding="utf-8")
    assert load_section_html(inline="<p>inline</p>", file_path=f) == "<p>from-file</p>"


def test_load_section_html_uses_inline_when_no_file():
    assert load_section_html(inline="<p>inline</p>", file_path=None) == "<p>inline</p>"


def test_compose_cli_reads_section_files(synthetic_ready_dir: Path, monkeypatch):
    import compose_html as mod

    fig_dir = synthetic_ready_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    (fig_dir / "奇异值与剔异前均值.png").write_bytes(b"x")
    sec = synthetic_ready_dir / "report_sections"
    sec.mkdir()
    (sec / "intro.html").write_text("<p>文件介绍</p>", encoding="utf-8")
    (sec / "sensitivity.html").write_text("<p>文件灵敏度</p>", encoding="utf-8")
    (sec / "curves_notes.html").write_text("<p>文件曲线</p>", encoding="utf-8")
    (sec / "conclusion.html").write_text("<p>文件结论</p>", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "compose_html.py",
            "--output-dir",
            str(synthetic_ready_dir),
            "--intro-file",
            str(sec / "intro.html"),
            "--sensitivity-file",
            str(sec / "sensitivity.html"),
            "--curves-notes-file",
            str(sec / "curves_notes.html"),
            "--conclusion-file",
            str(sec / "conclusion.html"),
        ],
    )
    mod.main()
    text = (synthetic_ready_dir / "report.html").read_text(encoding="utf-8")
    assert "文件介绍" in text
    assert "文件灵敏度" in text
    assert "文件曲线" in text
    assert "文件结论" in text


@pytest.mark.integration
def test_pdf_smoke(tmp_path: Path):
    from compose_pdf import html_to_pdf

    html = tmp_path / "t.html"
    html.write_text(
        "<html><body><h1>hi</h1></body></html>",
        encoding="utf-8",
    )
    try:
        pdf = html_to_pdf(html)
    except Exception as e:
        pytest.skip(f"playwright unavailable: {e}")
    assert pdf.is_file() and pdf.stat().st_size > 100
