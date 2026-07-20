# -*- coding: utf-8 -*-
"""Quantize numerics to 1 decimal for directivity reads."""
from __future__ import annotations


def q1(x: float | int | None) -> float | None:
    if x is None or x == "":
        return None
    return round(float(x), 1)


def q1_list(vals: list[float | None]) -> list[float | None]:
    return [q1(v) for v in vals]
