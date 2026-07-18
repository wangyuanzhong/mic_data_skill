# -*- coding: utf-8 -*-
from compose_html import compose_report_html
from render_figures import render_all_figures


def test_e2e_figures_and_html(synthetic_ready_dir):
    figs = render_all_figures(synthetic_ready_dir)
    assert figs
    html = compose_report_html(
        synthetic_ready_dir,
        intro_html="<p>产品测试</p>",
        sensitivity_html="<p>灵敏度表</p>",
        curves_notes_html="",
        conclusion_html="<p>结论</p>",
    )
    assert html.is_file()
    text = html.read_text(encoding="utf-8")
    assert "产品测试" in text
    assert "奇异值与剔异前均值.png" in text
