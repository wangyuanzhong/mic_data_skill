# -*- coding: utf-8 -*-
"""
run_cluster.py — Euclidean distance matrix + k=1 cluster suggestion.

For each non-axial delta_<tag> sheet, band-limit to [f_lo_hz, f_hi_hz],
compute sample×sample Euclidean distances (None pairs skipped), assign all
clusterable samples to one cluster (k=1 path; multi-k in a later task), and
write cluster_dist / cluster_suggest / cluster_meta / cluster_final (if missing).

Usage:
    python run_cluster.py --params <output_dir>/params.json
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from angle_sheets import normalize_angle_tag, read_angle_sheet
from params_io import load_params, resolve_under_output
from utf8_boot import ensure_utf8_stdio


def _replace_sheet(wb, name: str) -> Worksheet:
    if name in wb.sheetnames:
        del wb[name]
    return wb.create_sheet(name)


def _band_mask(freqs: list[float], f_lo: float, f_hi: float) -> list[bool]:
    return [f_lo <= float(f) <= f_hi for f in freqs]


def _euclid(a: list[float | None], b: list[float | None]) -> float | None:
    """Euclidean distance; only positions where both sides are non-None.

    Returns None if no overlapping valid points.
    """
    if len(a) != len(b):
        raise ValueError("vector length mismatch in _euclid")
    s = 0.0
    n = 0
    for va, vb in zip(a, b):
        if va is None or vb is None:
            continue
        d = float(va) - float(vb)
        s += d * d
        n += 1
    if n == 0:
        return None
    return math.sqrt(s)


def _band_columns(
    freqs: list[float],
    cols: list[list[float | None]],
    f_lo: float,
    f_hi: float,
) -> list[list[float | None]]:
    mask = _band_mask(freqs, f_lo, f_hi)
    return [[col[i] for i in range(len(freqs)) if mask[i]] for col in cols]


def _is_clusterable(vec: list[float | None]) -> bool:
    return any(v is not None for v in vec)


def _class_center(members: list[list[float | None]]) -> list[float | None]:
    if not members:
        return []
    n_freq = len(members[0])
    out: list[float | None] = []
    for i in range(n_freq):
        vals = [m[i] for m in members if m[i] is not None]
        if not vals:
            out.append(None)
        else:
            out.append(sum(vals) / len(vals))
    return out


def _write_dist(
    ws: Worksheet,
    samples: list[str],
    dist: list[list[float | None]],
) -> None:
    ws.append(["", *samples])
    for i, name in enumerate(samples):
        row: list = [name]
        for j in range(len(samples)):
            row.append(dist[i][j])
        ws.append(row)


def _write_suggest(
    ws: Worksheet,
    samples: list[str],
    cluster_ids: list[int | str],
    dist_to_center: list[float | None],
) -> None:
    ws.append(["sample", "cluster_id", "dist_to_center"])
    for name, cid, d in zip(samples, cluster_ids, dist_to_center):
        ws.append([name, cid, d])


def _write_meta(ws: Worksheet, *, chosen_k: int = 1) -> None:
    ws.append(["k", "silhouette", "chosen"])
    # Task 2: force k=1 path only
    ws.append([1, "N/A", "yes" if chosen_k == 1 else "no"])


def _write_final(
    ws: Worksheet,
    samples: list[str],
    cluster_ids: list[int | str],
) -> None:
    ws.append(["sample", "cluster_id", "cluster_name"])
    for name, cid in zip(samples, cluster_ids):
        if isinstance(cid, int):
            cname = f"类{cid}"
        else:
            cname = ""
        ws.append([name, cid, cname])


def _cluster_angle(
    wb,
    *,
    tag: str,
    freqs: list[float],
    samples: list[str],
    cols: list[list[float | None]],
    f_lo: float,
    f_hi: float,
) -> int:
    """Write cluster sheets for one angle. Returns 0 or 2."""
    band_cols = _band_columns(freqs, cols, f_lo, f_hi)
    clusterable = [_is_clusterable(c) for c in band_cols]
    n_clusterable = sum(1 for c in clusterable if c)
    if n_clusterable < 1:
        print(f"no clusterable samples for tag={tag!r}", file=sys.stderr)
        return 2

    n = len(samples)
    dist: list[list[float | None]] = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if not clusterable[i] or not clusterable[j]:
                dist[i][j] = None
                continue
            if i == j:
                dist[i][j] = 0.0
                continue
            d = _euclid(band_cols[i], band_cols[j])
            dist[i][j] = d

    # k=1: all clusterable → cluster 1
    cluster_ids: list[int | str] = []
    members: list[list[float | None]] = []
    for i in range(n):
        if clusterable[i]:
            cluster_ids.append(1)
            members.append(band_cols[i])
        else:
            cluster_ids.append("unclustered")

    center = _class_center(members)
    dist_to_center: list[float | None] = []
    for i in range(n):
        if not clusterable[i]:
            dist_to_center.append(None)
        else:
            dist_to_center.append(_euclid(band_cols[i], center))

    dist_name = f"cluster_dist_{tag}"
    suggest_name = f"cluster_suggest_{tag}"
    meta_name = f"cluster_meta_{tag}"
    final_name = f"cluster_final_{tag}"

    _write_dist(_replace_sheet(wb, dist_name), samples, dist)
    _write_suggest(
        _replace_sheet(wb, suggest_name), samples, cluster_ids, dist_to_center
    )
    _write_meta(_replace_sheet(wb, meta_name), chosen_k=1)

    if final_name not in wb.sheetnames:
        _write_final(_replace_sheet(wb, final_name), samples, cluster_ids)

    return 0


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Write cluster_* sheets from delta curves."
    )
    parser.add_argument("--params", required=True, type=Path)
    args = parser.parse_args(argv)

    params = load_params(args.params)
    xlsx_path = resolve_under_output(params, "process_xlsx", args.params)
    angles = params.get("angles") or []
    axial = params.get("axial_angle") or ""
    f_lo = float(params.get("f_lo_hz") or 0)
    f_hi = float(params.get("f_hi_hz") or 0)

    k_max_raw = params.get("cluster_k_max", 5)
    if isinstance(k_max_raw, bool) or not isinstance(k_max_raw, (int, float)):
        print(f"cluster_k_max must be numeric: {k_max_raw!r}", file=sys.stderr)
        return 2
    k_max = int(k_max_raw)
    if k_max <= 0:
        print(f"cluster_k_max must be > 0: {k_max}", file=sys.stderr)
        return 2

    if not angles:
        print("params.angles is empty", file=sys.stderr)
        return 2

    wb = load_workbook(xlsx_path)

    delta_sheets: list[tuple[str, str]] = []
    for angle in angles:
        if angle == axial:
            continue
        tag = normalize_angle_tag(angle)
        name = f"delta_{tag}"
        if name in wb.sheetnames:
            delta_sheets.append((angle, name))

    if not delta_sheets:
        print("no delta_* sheets found; run run_deltas first", file=sys.stderr)
        return 2

    written: list[str] = []
    for angle, delta_name in delta_sheets:
        freqs, samples, cols = read_angle_sheet(wb[delta_name])
        tag = normalize_angle_tag(angle)
        rc = _cluster_angle(
            wb,
            tag=tag,
            freqs=freqs,
            samples=samples,
            cols=cols,
            f_lo=f_lo,
            f_hi=f_hi,
        )
        if rc != 0:
            return rc
        written.append(tag)

    wb.save(xlsx_path)
    print(f"run_cluster: wrote sheets for {len(written)} angles: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
