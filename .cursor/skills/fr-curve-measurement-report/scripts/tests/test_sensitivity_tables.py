# -*- coding: utf-8 -*-
from sensitivity_tables import (
    count_sensitivity_bins_absolute,
    sensitivity_bin_count_html,
    sensitivity_detail_html,
)


def test_count_bins_absolute_from_relative():
    rows = [
        {"sample": "a", "bin_lo_db": 0.0, "bin_hi_db": 0.5},
        {"sample": "b", "bin_lo_db": 0.0, "bin_hi_db": 0.5},
        {"sample": "c", "bin_lo_db": 0.5, "bin_hi_db": 1.0},
    ]
    bins = count_sensitivity_bins_absolute(rows, midline=-40.0)
    assert bins[0] == (-40.0, -39.5, 2)
    assert bins[1] == (-39.5, -39.0, 1)


def test_count_html_absolute_single_cell(synthetic_ready_dir):
    html = sensitivity_bin_count_html(synthetic_ready_dir)
    assert "幅度范围" in html
    assert "样机数" in html
    assert "~" in html
    assert "幅度下限" not in html
    assert "pin" not in html.lower()
    # fixture midline -39.85 → q1 -39.9; bin 0~0.5 → absolute -39.9~-39.4
    assert "-39.9~-39.4" in html


def test_detail_html_lists_each_sample(synthetic_ready_dir):
    html = sensitivity_detail_html(synthetic_ready_dir)
    assert "灵敏度明细" in html
    assert "<table>" in html
    assert "S1" in html
    assert "S2" in html
    assert "S3" in html
    assert "S4" in html
    assert "1000Hz" in html or "level" in html.lower() or "dBV" in html
    assert "golden" in html or "金标" in html
