# -*- coding: utf-8 -*-
from compose_html import compose_report_html
from render_figures import render_all_figures


def test_e2e_figures_and_html(synthetic_ready_dir):
    figs = render_all_figures(synthetic_ready_dir)
    assert figs
    html = compose_report_html(
        synthetic_ready_dir,
        intro_note="产品测试",
        sensitivity_note="灵敏度说明",
        curves_notes="",
        conclusion_note="结论",
    )
    assert html.is_file()
    text = html.read_text(encoding="utf-8")
    assert "产品测试" in text
    assert "灵敏度明细" in text
    assert "奇异值与剔异前均值.png" in text
