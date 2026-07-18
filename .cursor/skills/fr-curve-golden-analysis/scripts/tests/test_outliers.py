# -*- coding: utf-8 -*-
"""Tests for high-Q exemption and outlier proposal."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from outliers import estimate_peak_q, propose_outliers  # noqa: E402


def _log_freqs(n: int = 200, f_lo: float = 100.0, f_hi: float = 15000.0) -> list[float]:
    """Log-spaced frequency grid."""
    log_lo, log_hi = math.log10(f_lo), math.log10(f_hi)
    return [10 ** (log_lo + (log_hi - log_lo) * i / (n - 1)) for i in range(n)]


def test_estimate_peak_q_narrow_spike_high_q():
    """Narrow Lorentz-like spike around 1kHz should yield Q >= 10."""
    freqs = _log_freqs(400)
    f0 = 1000.0
    # Half-power bandwidth for Q=20 → Δf = f0/Q = 50 Hz
    q_target = 20.0
    half_bw = f0 / q_target / 2.0  # HWHM in Hz (approx for -3dB of |dev|)
    peak = 5.0
    mean = [0.0] * len(freqs)
    sample = []
    for f in freqs:
        # |dev| peak shape: peak / (1 + ((f-f0)/half_bw)^2)  → -3dB at ±half_bw
        sample.append(peak / (1.0 + ((f - f0) / half_bw) ** 2))
    q, stable, f_at = estimate_peak_q(freqs, sample, mean, f_lo=100.0, f_hi=15000.0)
    assert stable is True
    assert f_at is not None
    assert abs(f_at - f0) / f0 < 0.05
    assert q is not None and q >= 10.0


def test_estimate_peak_q_broad_bump_low_q():
    """Very wide bump should be low Q / not high-Q."""
    freqs = _log_freqs(400)
    f0 = 1000.0
    half_bw = 400.0  # wide → low Q
    peak = 5.0  # need >3 dB so -3dB bandwidth is defined
    mean = [0.0] * len(freqs)
    sample = [peak / (1.0 + ((f - f0) / half_bw) ** 2) for f in freqs]
    q, stable, _ = estimate_peak_q(freqs, sample, mean, f_lo=100.0, f_hi=15000.0)
    assert stable is True
    assert q is not None and q < 10.0


def test_propose_outliers_exempts_high_q_keeps_broad():
    freqs = _log_freqs(300)
    mean = [0.0] * len(freqs)

    # Sample A: narrow high-Q spike (large peak but should be exempt)
    f0 = 800.0
    half_bw_a = f0 / 20.0 / 2.0
    spike = [5.0 / (1.0 + ((f - f0) / half_bw_a) ** 2) for f in freqs]

    # Sample B: broad elevated region (should be suggested)
    bump = [2.5 if 500 <= f <= 3000 else 0.05 for f in freqs]

    # Several near-mean samples so batch median stays low
    curves = {
        "spike": spike,
        "broad": bump,
        "quiet1": [0.05] * len(freqs),
        "quiet2": [0.04] * len(freqs),
        "quiet3": [0.06] * len(freqs),
        "quiet4": [0.05] * len(freqs),
    }

    rows = propose_outliers(
        freqs,
        curves,
        mean,
        f_lo=100.0,
        f_hi=15000.0,
        q_threshold=10.0,
        min_dev_db=1.0,
        median_factor=2.0,
    )
    by_id = {r["sample"]: r for r in rows}
    assert by_id["spike"]["exempt_high_q"] is True
    assert by_id["spike"]["suggest_exclude"] is False
    assert by_id["broad"]["exempt_high_q"] is False
    assert by_id["broad"]["suggest_exclude"] is True
    assert by_id["quiet1"]["suggest_exclude"] is False
