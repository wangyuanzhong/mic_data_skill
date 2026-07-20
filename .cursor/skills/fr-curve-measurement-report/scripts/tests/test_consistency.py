# -*- coding: utf-8 -*-
from consistency import compute_sigma_curve, summarize_consistency_zh


def test_sigma_zero_when_identical():
    freqs = [100.0, 1000.0, 10000.0]
    amps = {"a": [0.0, 0.0, 0.0], "b": [0.0, 0.0, 0.0]}
    out = compute_sigma_curve(freqs, amps, 100.0, 15000.0)
    assert out["sigma_db"] == [0.0, 0.0, 0.0]


def test_sigma_computed_outside_band():
    """Out-of-band points still get σ (display full curve; band is for analysis notes)."""
    freqs = [50.0, 1000.0, 20000.0]
    amps = {"a": [0.0, 1.0, 0.0], "b": [0.0, -1.0, 0.0]}
    out = compute_sigma_curve(freqs, amps, 100.0, 15000.0)
    assert out["sigma_db"][0] is not None
    assert out["sigma_db"][2] is not None
    assert out["sigma_db"][0] == 0.0
    assert out["sigma_db"][2] == 0.0
    assert out["sigma_db"][1] > 0


def test_summarize_mentions_bands():
    freqs = [100.0, 200.0, 1000.0, 2000.0, 8000.0]
    amps = {
        "a": [0.0, 0.0, 0.0, 0.0, 0.0],
        "b": [0.1, 0.1, 2.0, 0.2, 0.1],
    }
    sigma = compute_sigma_curve(freqs, amps, 100.0, 15000.0)
    text = summarize_consistency_zh(sigma)
    assert "较好" in text or "一般" in text or "偏弱" in text
    assert "Hz" in text
