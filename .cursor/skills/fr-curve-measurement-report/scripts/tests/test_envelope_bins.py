# -*- coding: utf-8 -*-
from envelope_bins import bin_samples_by_envelope, envelope_shell


def test_shell_edges():
    assert envelope_shell(0.1) == 0.5
    assert envelope_shell(0.5) == 0.5
    assert envelope_shell(0.6) == 1.0
    assert envelope_shell(1.0) == 1.0


def test_bin_groups():
    rows = [
        {"sample": "A", "delta": 0.2},
        {"sample": "B", "delta": 0.5},
        {"sample": "C", "delta": 0.8},
    ]
    bins = bin_samples_by_envelope(rows)
    assert bins[0.5] == ["A", "B"]
    assert bins[1.0] == ["C"]
    assert 1.5 not in bins
