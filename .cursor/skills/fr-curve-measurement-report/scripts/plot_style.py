# -*- coding: utf-8 -*-
"""Shared matplotlib helpers for FR report figures."""
from __future__ import annotations

import math

import matplotlib
from matplotlib.axes import Axes
from matplotlib.ticker import FixedLocator, FuncFormatter

# Prefer Windows CJK fonts so Chinese titles/legends render.
matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False


def format_hz(f: float) -> str:
    """Plain Hz label — no scientific notation."""
    if not math.isfinite(f) or f <= 0:
        return ""
    if abs(f - round(f)) < 0.05:
        return str(int(round(f)))
    if f >= 100:
        return f"{f:.0f}"
    return f"{f:.1f}".rstrip("0").rstrip(".")


def octave_centers(f_min: float, f_max: float) -> list[float]:
    """Full-octave centers overlapping [f_min, f_max] (ref 1000 Hz): …125,250,500,1k…"""
    if f_max < f_min:
        f_min, f_max = f_max, f_min
    centers: list[float] = []
    n = -20
    while n <= 20:
        f = 1000.0 * (2.0**n)
        if f > f_max * 1.02:
            break
        if f >= f_min * 0.98:
            centers.append(f)
        n += 1
    return centers


def third_octave_centers(f_min: float, f_max: float) -> list[float]:
    """1/3-octave preferred centers overlapping [f_min, f_max] (ref 1000 Hz)."""
    if f_max < f_min:
        f_min, f_max = f_max, f_min
    centers: list[float] = []
    n = -40
    while n <= 40:
        f = 1000.0 * (2.0 ** (n / 3.0))
        if f > f_max * 1.02:
            break
        if f >= f_min * 0.98:
            centers.append(f)
        n += 1
    return centers


def _is_near(f: float, targets: list[float], rel: float = 0.02) -> bool:
    return any(abs(f - t) / t <= rel for t in targets if t > 0)


REPORT_F_MIN_HZ = 20.0
REPORT_F_MAX_HZ = 20000.0


def setup_log_freq_axis(
    ax: Axes,
    f_min: float = REPORT_F_MIN_HZ,
    f_max: float = REPORT_F_MAX_HZ,
) -> None:
    """
    Log frequency axis fixed to report span (default 20–20000 Hz):
    - Labels: full-octave only (no sci notation)
    - Grid: octave = stronger; 1/3-octave = thinner/lighter (no labels)
    Analysis-band limits are NOT ticks — draw them separately with draw_analysis_band.
    """
    ax.set_xscale("log")
    ax.set_xlim(f_min, f_max)
    ax.set_xlabel("频率 (Hz)")

    octaves = octave_centers(f_min, f_max)
    thirds = third_octave_centers(f_min, f_max)

    ax.grid(False)
    for t in thirds:
        if _is_near(t, octaves):
            continue
        ax.axvline(t, color="0.88", linewidth=0.45, zorder=0)
    for t in octaves:
        ax.axvline(t, color="0.55", linewidth=0.95, zorder=0)

    ax.xaxis.set_major_locator(FixedLocator(octaves))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _pos: format_hz(v)))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    for label in ax.get_xticklabels():
        label.set_rotation(0)
        label.set_ha("center")
        label.set_fontsize(8)


def draw_analysis_band(ax: Axes, f_lo: float, f_hi: float) -> None:
    ax.axvline(f_lo, color="0.35", linestyle="--", linewidth=1.2, alpha=0.9, zorder=3)
    ax.axvline(f_hi, color="0.35", linestyle="--", linewidth=1.2, alpha=0.9, zorder=3)
    for f in (f_lo, f_hi):
        ax.annotate(
            f"{format_hz(f)} Hz",
            xy=(f, 0.0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -28),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            color="0.25",
            fontweight="bold",
            clip_on=False,
        )


def draw_envelope_box(ax: Axes, f_lo: float, f_hi: float, shell_db: float) -> None:
    """Thick red ±shell horizontal lines only inside analysis band."""
    ax.hlines(
        shell_db,
        f_lo,
        f_hi,
        colors="red",
        linewidths=2.4,
        zorder=5,
    )
    ax.hlines(
        -shell_db,
        f_lo,
        f_hi,
        colors="red",
        linewidths=2.4,
        zorder=5,
    )
