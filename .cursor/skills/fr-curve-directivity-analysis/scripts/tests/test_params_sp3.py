# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "references" / "params.template.json"


def test_params_template_has_sp3_fields():
    data = json.loads(REF.read_text(encoding="utf-8"))
    assert data["cluster_k_max"] == 5
    assert data["peak_prominence_db"] == 1.0
    assert abs(float(data["peak_min_octave"]) - (1.0 / 3.0)) < 1e-9
    assert data["peak_include_q"] is True


def test_scipy_importable():
    import scipy  # noqa: F401
    from scipy.signal import find_peaks  # noqa: F401
