# -*- coding: utf-8 -*-
"""Batch curve consistency σ(f) relative to mean (bk-tool style)."""
from __future__ import annotations


def _std_dev(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    return var ** 0.5


def compute_sigma_curve(
    freqs: list[float],
    amps_by_sample: dict[str, list[float]],
    f_lo: float,
    f_hi: float,
) -> dict:
    names = list(amps_by_sample.keys())
    if len(names) < 2:
        raise ValueError("参与一致性分析至少需要 2 条曲线")
    n_f = len(freqs)
    for name, amps in amps_by_sample.items():
        if len(amps) != n_f:
            raise ValueError(f"曲线长度不一致: {name}")

    sigma_db: list[float | None] = []
    for j, f in enumerate(freqs):
        if f < f_lo or f > f_hi:
            sigma_db.append(None)
            continue
        vals = [amps_by_sample[n][j] for n in names]
        mean = sum(vals) / len(vals)
        devs = [v - mean for v in vals]
        sigma_db.append(round(_std_dev(devs), 1))

    return {
        "freqs_hz": list(freqs),
        "sigma_db": sigma_db,
        "f_lo": f_lo,
        "f_hi": f_hi,
        "curve_count": len(names),
    }


def _third_octave_band_edges(fc: float) -> tuple[float, float]:
    ratio = 2.0 ** (1.0 / 6.0)
    return fc / ratio, fc * ratio


def _format_hz_plain(f: float) -> str:
    if abs(f - round(f)) < 0.05:
        return str(int(round(f)))
    return f"{f:.1f}".rstrip("0").rstrip(".")


def summarize_consistency_zh(sigma: dict) -> str:
    """Deterministic Chinese blurb: overall + best/worst 1/3-octave bands."""
    freqs = sigma["freqs_hz"]
    sigmas = sigma["sigma_db"]
    f_lo = float(sigma["f_lo"])
    f_hi = float(sigma["f_hi"])
    n = int(sigma.get("curve_count") or 0)

    points = [
        (float(f), float(s))
        for f, s in zip(freqs, sigmas)
        if s is not None and f_lo <= f <= f_hi
    ]
    if not points:
        return "分析频段内无有效 σ 数据，无法评价一致性。"

    vals = [s for _, s in points]
    mean_s = sum(vals) / len(vals)
    max_s = max(vals)
    max_f = next(f for f, s in points if s == max_s)

    # 1/3 octave band means within analysis range
    bands: list[tuple[float, float, int]] = []
    n_idx = -40
    while n_idx <= 40:
        fc = 1000.0 * (2.0 ** (n_idx / 3.0))
        n_idx += 1
        if fc > f_hi * 1.05:
            break
        lo, hi = _third_octave_band_edges(fc)
        if hi < f_lo or lo > f_hi:
            continue
        band_vals = [s for f, s in points if lo <= f <= hi]
        if len(band_vals) < 1:
            continue
        bands.append((fc, sum(band_vals) / len(band_vals), len(band_vals)))

    lines = [
        f"本批共 {n} 条曲线参与一致性；分析频段 {_format_hz_plain(f_lo)}–{_format_hz_plain(f_hi)} Hz。",
        f"带内 σ 平均约 {mean_s:.1f} dB，最大约 {max_s:.1f} dB（约 {_format_hz_plain(max_f)} Hz）。",
    ]
    if mean_s < 0.5:
        lines.append("整体一致性较好（平均 σ 偏低）。")
    elif mean_s < 1.0:
        lines.append("整体一致性一般，局部频段仍有散开。")
    else:
        lines.append("整体一致性偏弱，部分频段样机间差异明显。")

    if bands:
        by_good = sorted(bands, key=lambda t: (t[1], t[0]))
        by_bad = sorted(bands, key=lambda t: (-t[1], t[0]))
        good = by_good[:2]
        bad = by_bad[:2]
        good_txt = "、".join(
            f"{_format_hz_plain(fc)} Hz 一带（σ≈{sig:.1f} dB）" for fc, sig, _ in good
        )
        bad_txt = "、".join(
            f"{_format_hz_plain(fc)} Hz 一带（σ≈{sig:.1f} dB）" for fc, sig, _ in bad
        )
        lines.append(f"相对较好的频段：{good_txt}。")
        lines.append(f"相对较差的频段：{bad_txt}。")

    return "\n".join(lines)
