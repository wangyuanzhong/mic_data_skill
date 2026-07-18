# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from gates import check_report_ready


def test_missing_params_raises(tmp_path: Path):
    with pytest.raises(SystemExit, match="params.json"):
        check_report_ready(tmp_path)


def test_pending_outlier_gate_raises(synthetic_pending_dir: Path):
    with pytest.raises(SystemExit, match="outlier_gate"):
        check_report_ready(synthetic_pending_dir)


def test_confirmed_passes(synthetic_ready_dir: Path):
    check_report_ready(synthetic_ready_dir)
