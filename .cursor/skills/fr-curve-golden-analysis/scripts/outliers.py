# -*- coding: utf-8 -*-
"""Outlier proposal with high-Q peak/valley exemption."""
from __future__ import annotations

import math
import statistics
from typing import Any


def _deviations(
    freqs: list[float],
    sample: list[float],
    mean: list[float],
    f_lo: float,
    f_hi: float,
) -> list[tuple[float, float]]:
    """Return (freq, signed_dev) in analysis band."""
    out: list[tuple[float, float]] = []
    for f, s, m in zip(freqs, sample, mean):
        if f < f_lo or f > f_hi:
            continue
        if s is None or m is None:
            continue
        out.append((float(f), float(s) - float(m)))
    return out


def estimate_peak_q(
    freqs: list[float],
    sample: list[float],
    mean: list[float],
    f_lo: float = 100.0,
    f_hi: float = 15000.0,
) -> tuple[float | None, bool, float | None]:
    """
    Estimate Q at the band max-|dev| peak/valley.

    Q = f0 / Δf where Δf is the -3 dB bandwidth of |dev| relative to the peak.
    Returns (q, stable, f0). stable=False if bandwidth cannot be resolved.
    """
    devs = _deviations(freqs, sample, mean, f_lo, f_hi)
    if not devs:
        return None, False, None

    # Prefer absolute max; if ties, lowest frequency
    max_abs = max(abs(d) for _, d in devs)
    if max_abs < 1e-12:
        return None, False, None
    candidates = [f for f, d in devs if abs(abs(d) - max_abs) < 1e-9]
    f0 = min(candidates)
    # Work on |dev| for bandwidth; -3dB of peak height in dB domain
    threshold = max_abs - 3.0
    if threshold <= 0:
        # Peak shorter than 3 dB — cannot define -3dB points relative to peak
        return None, False, None

    # Find left / right crossings of |dev| vs threshold around f0
    # Walk sorted by frequency (devs already in freq order if freqs sorted)
    abs_curve = [(f, abs(d)) for f, d in devs]
    # index of f0
    try:
        i0 = next(i for i, (f, _) in enumerate(abs_curve) if f == f0)
    except StopIteration:
        return None, False, None

    def _crossing(i_start: int, step: int) -> float | None:
        """Linear interpolate freq where |dev| crosses threshold."""
        i = i_start
        while 0 <= i + step < len(abs_curve):
            f1, a1 = abs_curve[i]
            f2, a2 = abs_curve[i + step]
            # crossing when one side >= threshold and other < threshold
            # moving outward from peak: expect a1 >= threshold near peak
            if (a1 - threshold) * (a2 - threshold) <= 0 and a1 != a2:
                # interpolate
                t = (threshold - a1) / (a2 - a1)
                return f1 + t * (f2 - f1)
            if a2 < threshold and a1 < threshold:
                # already below without clear bracket — stop
                return None
            i += step
        return None

    f_left = _crossing(i0, -1)
    f_right = _crossing(i0, +1)
    if f_left is None or f_right is None:
        return None, False, f0
    bw = abs(f_right - f_left)
    if bw <= 0:
        return None, False, f0
    q = f0 / bw
    # Sanity: ignore absurd Q from numerical noise
    if not math.isfinite(q) or q <= 0:
        return None, False, f0
    return float(q), True, float(f0)


def propose_outliers(
    freqs: list[float],
    samples: dict[str, list[float]],
    mean: list[float],
    f_lo: float = 100.0,
    f_hi: float = 15000.0,
    q_threshold: float = 10.0,
    min_dev_db: float = 1.0,
    median_factor: float = 2.0,
) -> list[dict[str, Any]]:
    """
    Propose outliers relative to mean curve.

    High-Q (Q >= q_threshold) peaks that dominate max |dev| are exempt
    (appear in review but suggest_exclude=False).
    """
    per_sample: list[dict[str, Any]] = []
    max_abs_list: list[float] = []

    for name, curve in samples.items():
        devs = _deviations(freqs, curve, mean, f_lo, f_hi)
        if not devs:
            row = {
                "sample": name,
                "max_abs_dev_db": None,
                "freq_at_max_hz": None,
                "q_estimate": None,
                "q_stable": False,
                "exempt_high_q": False,
                "exempt_reason": "no points in analysis band",
                "suggest_exclude": False,
                "suggest_reason": "no points in analysis band",
            }
            per_sample.append(row)
            continue

        max_abs = max(abs(d) for _, d in devs)
        freq_at = min(f for f, d in devs if abs(abs(d) - max_abs) < 1e-9)
        q, stable, f_q = estimate_peak_q(freqs, curve, mean, f_lo, f_hi)
        exempt = bool(stable and q is not None and q >= q_threshold)
        exempt_reason = ""
        if exempt:
            exempt_reason = f"豁免（高Q≥{q_threshold:g}）Q={q:.3g} @ {f_q:g}Hz"
        elif not stable:
            exempt_reason = "无法稳定估Q，不给高Q豁免"
        else:
            exempt_reason = f"Q={q:.3g} < {q_threshold:g}，不豁免"

        per_sample.append(
            {
                "sample": name,
                "max_abs_dev_db": max_abs,
                "freq_at_max_hz": freq_at,
                "q_estimate": q,
                "q_stable": stable,
                "exempt_high_q": exempt,
                "exempt_reason": exempt_reason,
                "suggest_exclude": False,  # filled below
                "suggest_reason": "",
            }
        )
        max_abs_list.append(max_abs)

    median_max = statistics.median(max_abs_list) if max_abs_list else 0.0
    threshold = max(min_dev_db, median_factor * median_max)

    for row in per_sample:
        mad = row["max_abs_dev_db"]
        if mad is None:
            continue
        if row["exempt_high_q"]:
            row["suggest_exclude"] = False
            row["suggest_reason"] = row["exempt_reason"]
            row["median_max_abs_db"] = median_max
            row["threshold_db"] = threshold
            continue
        if mad >= threshold:
            row["suggest_exclude"] = True
            row["suggest_reason"] = (
                f"max|dev|={mad:.3g}dB ≥ 门槛 {threshold:.3g}dB "
                f"(max(1.0, {median_factor:g}×中位数{median_max:.3g}))，且非高Q豁免"
            )
        else:
            row["suggest_exclude"] = False
            row["suggest_reason"] = (
                f"max|dev|={mad:.3g}dB < 门槛 {threshold:.3g}dB，不建议剔除"
            )
        row["median_max_abs_db"] = median_max
        row["threshold_db"] = threshold

    # Ensure median/threshold keys exist for empty-band rows
    for row in per_sample:
        row.setdefault("median_max_abs_db", median_max)
        row.setdefault("threshold_db", threshold)

    return per_sample
