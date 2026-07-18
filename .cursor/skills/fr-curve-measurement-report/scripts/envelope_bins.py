# -*- coding: utf-8 -*-
"""Group samples into 0.5 dB envelope shells from ranking delta."""
from __future__ import annotations

import math
from collections import defaultdict


def envelope_shell(delta: float, step: float = 0.5) -> float:
    if delta <= 0:
        return step
    return math.ceil(delta / step - 1e-12) * step


def bin_samples_by_envelope(
    rows: list[dict],
    step: float = 0.5,
    delta_key: str = "delta",
    sample_key: str = "sample",
) -> dict[float, list[str]]:
    """Map shell upper edge → sample names. Empty shells omitted."""
    buckets: dict[float, list[str]] = defaultdict(list)
    for row in rows:
        delta = float(row[delta_key])
        name = str(row[sample_key])
        buckets[envelope_shell(delta, step)].append(name)
    return {k: buckets[k] for k in sorted(buckets)}
