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
    - Vertical grid: octave = stronger; 1/3-octave = thinner/lighter (no labels)
    - Horizontal grid: major + minor dotted lines (same spirit as directivity plots)
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

    # Horizontal grid only (x already drawn via octave / 1/3 axvline above)
    ax.minorticks_on()
    ax.yaxis.grid(True, which="major", linestyle=":", linewidth=0.4, alpha=0.6, zorder=0)
    ax.yaxis.grid(True, which="minor", linestyle=":", linewidth=0.3, alpha=0.45, zorder=0)

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


# Dense FR only: sparse / mid-density traces must stay untouched.
SMOOTH_MIN_POINTS = 1000
DISPLAY_TARGET_POINTS = 500


def _light_ma(seg: list[float], window: int = 3) -> list[float]:
    if window < 3 or len(seg) < window:
        return seg
    if window % 2 == 0:
        window += 1
    half = window // 2
    padded = [seg[0]] * half + seg + [seg[-1]] * half
    acc = sum(padded[:window])
    out = [acc / window]
    for i in range(1, len(seg)):
        acc += padded[i + window - 1] - padded[i - 1]
        out.append(acc / window)
    return out


def prepare_curve_for_display(
    freqs: list[float],
    values: list[float | None] | list[float],
    *,
    min_points: int = SMOOTH_MIN_POINTS,
    target_points: int = DISPLAY_TARGET_POINTS,
) -> tuple[list[float], list[float]]:
    """
    Display-only. Below min_points → identity. Dense → average into uniform
    log-frequency bins (plus a tiny neighbor MA). Analysis sheets untouched.
    """
    ys = [float("nan") if v is None else float(v) for v in values]
    pairs: list[tuple[float, float]] = []
    for f, y in zip(freqs, ys):
        try:
            ff = float(f)
            yy = float(y)
        except (TypeError, ValueError):
            continue
        if math.isfinite(ff) and math.isfinite(yy) and ff > 0:
            pairs.append((ff, yy))
    if len(pairs) < min_points:
        return [float(f) for f in freqs], ys

    pairs.sort(key=lambda p: p[0])
    f0, f1 = pairs[0][0], pairs[-1][0]
    if f1 <= f0:
        return [float(f) for f in freqs], ys

    n_bins = min(target_points, max(2, len(pairs) // 2))
    if n_bins < 2 or n_bins >= len(pairs):
        return [float(f) for f in freqs], ys

    log0, log1 = math.log(f0), math.log(f1)
    span = log1 - log0
    bin_f: list[list[float]] = [[] for _ in range(n_bins)]
    bin_y: list[list[float]] = [[] for _ in range(n_bins)]
    for f, y in pairs:
        t = (math.log(f) - log0) / span
        i = min(n_bins - 1, max(0, int(t * n_bins)))
        bin_f[i].append(f)
        bin_y[i].append(y)

    out_f: list[float] = []
    out_y: list[float] = []
    for bf, by in zip(bin_f, bin_y):
        if not by:
            continue
        out_f.append(math.exp(sum(math.log(f) for f in bf) / len(bf)))
        out_y.append(sum(by) / len(by))

    # slight log-neighbor soften (window=3) — not a heavy wipe
    if len(out_y) >= 5:
        out_y = _light_ma(out_y, 3)
    return out_f, out_y


def smooth_series_for_display(
    values: list[float | None] | list[float],
    *,
    min_points: int = SMOOTH_MIN_POINTS,
    target_points: int = DISPLAY_TARGET_POINTS,
) -> list[float]:
    """Display-only: synthetic index freqs → log-bin path via prepare_*."""
    ys = [float("nan") if v is None else float(v) for v in values]
    idxs = [i for i, v in enumerate(ys) if math.isfinite(v)]
    if len(idxs) < min_points:
        return ys
    # index-as-Hz is meaningless for log bins; keep light index block mean
    block = max(1, (len(idxs) + target_points - 1) // target_points)
    if block < 2:
        return ys
    out = ys[:]
    for start in range(0, len(idxs), block):
        group = idxs[start : start + block]
        mean = sum(ys[i] for i in group) / len(group)
        for i in group:
            out[i] = mean
    return out


def clamp_sigma_ylim(ax: Axes) -> None:
    """σ(f) is non-negative; never show a negative lower limit."""
    _lo, hi = ax.get_ylim()
    ax.set_ylim(bottom=0.0, top=max(float(hi), 0.0))
