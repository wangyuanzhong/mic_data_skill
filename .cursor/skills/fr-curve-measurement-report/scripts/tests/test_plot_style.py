# -*- coding: utf-8 -*-
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import (
    REPORT_F_MAX_HZ,
    REPORT_F_MIN_HZ,
    clamp_sigma_ylim,
    format_hz,
    octave_centers,
    prepare_curve_for_display,
    smooth_series_for_display,
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


def test_smooth_skips_sparse_series():
    ys = [math.sin(i / 3) for i in range(80)]
    out = smooth_series_for_display(ys)
    assert out == ys


def test_smooth_skips_mid_density_series():
    # typical 1/3-octave / mid FR — must not be wiped smooth
    freqs = [100 * (1.05**i) for i in range(400)]
    ys = [math.sin(i / 8) for i in range(400)]
    xf, yo = prepare_curve_for_display(freqs, ys)
    assert xf == [float(f) for f in freqs]
    assert yo == ys


def test_prepare_dense_uses_log_bins():
    # linear-in-Hz dense grid (like B&K) → display should rebin in log-f
    freqs = [20.0 + i * (20000.0 - 20.0) / 5999 for i in range(6000)]
    ys = [0.2 * math.sin(i / 200) + 0.05 * ((i % 7) - 3) for i in range(6000)]
    xf, yo = prepare_curve_for_display(freqs, ys)
    assert len(xf) == len(yo)
    assert len(xf) < len(freqs)
    assert 300 <= len(xf) <= 700
    # log steps of output should be much more uniform than linear-Hz input
    log_in = [math.log(f) for f in freqs]
    log_out = [math.log(f) for f in xf]
    din = [log_in[i] - log_in[i - 1] for i in range(1, len(log_in))]
    dout = [log_out[i] - log_out[i - 1] for i in range(1, len(log_out))]

    def cv(seq: list[float]) -> float:
        m = sum(seq) / len(seq)
        var = sum((x - m) ** 2 for x in seq) / len(seq)
        return math.sqrt(var) / m

    assert cv(dout) < cv(din) * 0.35


def test_sigma_ylim_non_negative():
    fig, ax = plt.subplots()
    ax.plot([200, 1000, 20000], [0.2, 0.0, 0.5])
    ax.set_ylim(-1.0, 1.0)
    clamp_sigma_ylim(ax)
    lo, hi = ax.get_ylim()
    assert lo >= 0.0 - 1e-12
    assert hi >= 0.5
    plt.close(fig)


def test_setup_log_freq_axis_span_and_y_grid():
    from plot_style import setup_log_freq_axis

    fig, ax = plt.subplots()
    setup_log_freq_axis(ax)
    lo, hi = ax.get_xlim()
    assert abs(lo - REPORT_F_MIN_HZ) / REPORT_F_MIN_HZ < 0.05
    assert abs(hi - REPORT_F_MAX_HZ) / REPORT_F_MAX_HZ < 0.05
    # horizontal grid on (major)
    assert ax.yaxis._major_tick_kw.get("gridOn", False) or any(
        line.get_visible() for line in ax.get_ygridlines()
    )
    plt.close(fig)
