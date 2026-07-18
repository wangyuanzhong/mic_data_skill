# -*- coding: utf-8 -*-
"""Deterministic HTML section builders (tables from params/xlsx; notes from Agent)."""
from __future__ import annotations

import html
from typing import Any

from sensitivity_tables import sensitivity_bin_count_html, sensitivity_detail_html


def _as_note_html(note: str) -> str:
    note = (note or "").strip()
    if not note:
        return ""
    if "<" in note and ">" in note:
        return note
    paras = []
    for block in note.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = "<br/>".join(html.escape(line) for line in block.splitlines())
        paras.append(f"<p>{lines}</p>")
    return "\n".join(paras)


def build_intro_html(params: dict[str, Any], note: str = "") -> str:
    product = params.get("product") or ""
    note_s = params.get("note") or "无"
    unit = params.get("unit") or ""
    f_lo = params.get("f_lo_hz", "")
    f_hi = params.get("f_hi_hz", "")
    sens = params.get("sensitivity") or {}
    mode = sens.get("midline_mode") or ""
    mid_db = sens.get("midline_db")
    if mode == "mean":
        mid_label = "批平均（mean）"
    elif mode == "value" and mid_db is not None:
        mid_label = f"设计值 {mid_db}"
    else:
        mid_label = str(mode or "—")
    curves = params.get("curves") or {}
    excl = curves.get("exclude")
    if excl is None:
        excl_label = "未确认"
    elif excl == []:
        excl_label = "无"
    else:
        excl_label = ", ".join(str(x) for x in excl)

    table = f"""<table>
<tr><th>项</th><th>内容</th></tr>
<tr><td>型号/产品</td><td>{html.escape(str(product))}</td></tr>
<tr><td>说明</td><td>{html.escape(str(note_s))}</td></tr>
<tr><td>幅度单位</td><td>{html.escape(str(unit))}</td></tr>
<tr><td>分析频率范围</td><td>{html.escape(str(f_lo))}–{html.escape(str(f_hi))} Hz</td></tr>
<tr><td>灵敏度中线</td><td>{html.escape(mid_label)}</td></tr>
<tr><td>曲线剔除</td><td>{html.escape(excl_label)}</td></tr>
</table>"""
    parts = [table]
    note_html = _as_note_html(note)
    if note_html:
        parts.append(note_html)
    else:
        parts.append(
            "<p>本报告基于本批测量选标结果：灵敏度与曲线标准见后文。</p>"
        )
    return "\n".join(parts)


def build_sensitivity_html(output_dir, note: str = "") -> str:
    parts: list[str] = []
    note_html = _as_note_html(note)
    if note_html:
        parts.append(note_html)
    detail = sensitivity_detail_html(output_dir)
    if detail:
        parts.append(detail)
    count = sensitivity_bin_count_html(output_dir)
    if count:
        parts.append(count)
    return "\n".join(parts)
