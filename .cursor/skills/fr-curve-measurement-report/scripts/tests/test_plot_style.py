# -*- coding: utf-8 -*-
from plot_style import (
    REPORT_F_MAX_HZ,
    REPORT_F_MIN_HZ,
    format_hz,
    octave_centers,
    third_octave_centers,
)


def test_format_hz_no_scientific():
    assert format_hz(1000) == "1000"
    assert "e" not in format_hz(10000).lower()
    assert format_hz(125.0) == "125"


def test_octave_includes_1k():
    centers = octave_centers(REPORT_F_MIN_HZ, REPORT_F_MAX_HZ)
    assert any(abs(c - 1000) < 1 for c in centers)
    assert centers == sorted(centers)


def test_third_octave_denser_than_octave():
    assert len(third_octave_centers(REPORT_F_MIN_HZ, REPORT_F_MAX_HZ)) > len(
        octave_centers(REPORT_F_MIN_HZ, REPORT_F_MAX_HZ)
    )


def test_report_axis_defaults():
    assert REPORT_F_MIN_HZ == 20.0
    assert REPORT_F_MAX_HZ == 20000.0
