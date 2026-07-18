# -*- coding: utf-8 -*-
from sensitivity_tables import (
    count_sensitivity_bins_absolute,
    sensitivity_bin_count_html,
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
    # fixture midline -39.85, bin 0~0.5 → absolute about -39.85~-39.35
    assert "-39.85~-39.35" in html or "-39.85~" in html
