# -*- coding: utf-8 -*-
"""Compose directivity report.html from figures + Agent notes + sheet tables.

Notes are CLI fill-ins; the script persists them under report_sections/ and
builds the intro table + consistency summary table from params.json /
process.xlsx. The Agent never hand-writes report.html or report_sections/.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from openpyxl import load_workbook

from angle_sheets import normalize_angle_tag
from params_io import resolve_under_output
from utf8_boot import ensure_utf8_stdio, read_text, write_text


def _as_note_html(text: str) -> str:
    if not text or not text.strip():
        return ""
    paras = "".join(
        f"<p>{html.escape(line)}</p>" for line in text.splitlines() if line.strip()
    )
    return f'<div class="figure-note">{paras}</div>' if paras else ""


def write_note_files(
    output_dir: Path,
    *,
    intro_note: str = "",
    deltas_note: str = "",
    consistency_note: str = "",
    conclusion_note: str = "",
) -> Path:
    sec = Path(output_dir) / "report_sections"
    sec.mkdir(parents=True, exist_ok=True)
    mapping = {
        "intro_note.txt": intro_note,
        "deltas_note.txt": deltas_note,
        "consistency_note.txt": consistency_note,
        "conclusion_note.txt": conclusion_note,
    }
    for name, text in mapping.items():
        body = text or ""
        if body and not body.endswith("\n"):
            body += "\n"
        write_text(sec / name, body)
    return sec


def build_intro_html(params: dict, intro_note: str) -> str:
    rows = [
        ("产品", params.get("product") or ""),
        ("说明", params.get("note") or "无"),
        ("幅度单位", params.get("unit") or ""),
        ("分析频段", f"{params.get('f_lo_hz')}–{params.get('f_hi_hz')} Hz"),
        ("角度列表", ", ".join(params.get("angles") or []) or "—"),
        ("轴向参考", params.get("axial_angle") or "—"),
        ("样机数", str(params.get("sample_count") or "—")),
    ]
    body = "<table><tbody>"
    for k, v in rows:
        body += f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>"
    body += "</tbody></table>"
    if intro_note.strip():
        body += _as_note_html(intro_note)
    return body


def build_consistency_summary_html(output_dir: Path) -> str:
    xlsx_path = output_dir / "process.xlsx"
    if not xlsx_path.is_file():
        return ""
    wb = load_workbook(xlsx_path)
    if "consistency_summary" not in wb.sheetnames:
        return ""
    ws = wb["consistency_summary"]
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    body = '<h3>各角度一致性汇总</h3><table><thead><tr>'
    body += "".join(f"<th>{html.escape(str(h or ''))}</th>" for h in headers)
    body += "</tr></thead><tbody>"
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 1).value is None:
            break
        body += "<tr>"
        for c in range(1, len(headers) + 1):
            v = ws.cell(r, c).value
            body += f"<td>{html.escape(str(v if v is not None else ''))}</td>"
        body += "</tr>"
    body += "</tbody></table>"
    return body


def build_freq_bins_html(output_dir: Path, params: dict) -> str:
    """Render freq_bins detail + summary tables per non-axial angle.

    Returns "" if focus_freqs is empty or no freq_bins sheets exist.
    Raises SystemExit(2) if focus_freqs non-empty but a required sheet is missing.
    """
    focus_freqs = params.get("focus_freqs") or []
    if not focus_freqs:
        return ""
    angles = params.get("angles") or []
    axial = params.get("axial_angle") or ""
    xlsx_path = output_dir / "process.xlsx"
    if not xlsx_path.is_file():
        return ""
    wb = load_workbook(xlsx_path)

    body = ''
    for angle in angles:
        if angle == axial:
            continue
        tag = normalize_angle_tag(angle)
        detail_name = f"freq_bins_{tag}"
        summary_name = f"freq_bins_summary_{tag}"
        if detail_name not in wb.sheetnames:
            raise SystemExit(2)
        if summary_name not in wb.sheetnames:
            raise SystemExit(2)
        body += f'<h3>角度 {html.escape(str(angle))}</h3>'

        # detail table
        ws_d = wb[detail_name]
        body += '<table class="freq-bins-detail"><thead><tr>'
        for c in range(1, ws_d.max_column + 1):
            h = ws_d.cell(1, c).value
            body += f"<th>{html.escape(str(h or ''))}</th>"
        body += "</tr></thead><tbody>"
        for r in range(2, ws_d.max_row + 1):
            body += "<tr>"
            for c in range(1, ws_d.max_column + 1):
                v = ws_d.cell(r, c).value
                body += f"<td>{html.escape(str(v if v is not None else ''))}</td>"
            body += "</tr>"
        body += "</tbody></table>"

        # summary table
        ws_s = wb[summary_name]
        body += '<table class="freq-bins-summary"><thead><tr>'
        for c in range(1, ws_s.max_column + 1):
            h = ws_s.cell(1, c).value
            body += f"<th>{html.escape(str(h or ''))}</th>"
        body += "</tr></thead><tbody>"
        for r in range(2, ws_s.max_row + 1):
            if all(ws_s.cell(r, c).value is None for c in range(1, ws_s.max_column + 1)):
                continue
            body += "<tr>"
            for c in range(1, ws_s.max_column + 1):
                v = ws_s.cell(r, c).value
                body += f"<td>{html.escape(str(v if v is not None else ''))}</td>"
            body += "</tr>"
        body += "</tbody></table>"
    return body


def list_delta_figures(figures_dir: Path) -> list[Path]:
    return sorted(figures_dir.glob("差值叠图_*.png"))


def list_consistency_figures(figures_dir: Path) -> list[Path]:
    return sorted(figures_dir.glob("一致性sigma*.png"))


def compose_report_html(
    output_dir: Path,
    *,
    intro_note: str = "",
    deltas_note: str = "",
    consistency_note: str = "",
    conclusion_note: str = "",
    figures_dir: Path | None = None,
    persist_notes: bool = True,
) -> Path:
    output_dir = Path(output_dir)
    if persist_notes:
        write_note_files(
            output_dir,
            intro_note=intro_note,
            deltas_note=deltas_note,
            consistency_note=consistency_note,
            conclusion_note=conclusion_note,
        )
    figures_dir = Path(figures_dir) if figures_dir else output_dir / "figures"
    params: dict = {}
    params_path = output_dir / "params.json"
    if params_path.is_file():
        params = json.loads(read_text(params_path))

    delta_blocks = [
        {"src": (Path("figures") / p.name).as_posix(), "caption": p.stem}
        for p in list_delta_figures(figures_dir)
    ]
    consistency_blocks = [
        {"src": (Path("figures") / p.name).as_posix(), "caption": p.stem}
        for p in list_consistency_figures(figures_dir)
    ]

    intro_html = build_intro_html(params, intro_note)
    deltas_notes_html = _as_note_html(deltas_note)
    consistency_notes_html = _as_note_html(consistency_note)
    freq_bins_html = build_freq_bins_html(output_dir, params)
    consistency_summary_html = build_consistency_summary_html(output_dir)
    conclusion_html = _as_note_html(conclusion_note) or "<p></p>"

    tpl_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    css = read_text(tpl_dir / "report.css")
    tpl = env.get_template("report.html.j2")
    rendered = tpl.render(
        product=params.get("product") or "指向性分析报告",
        css=css,
        intro_html=intro_html,
        deltas_notes_html=deltas_notes_html,
        delta_figures=delta_blocks,
        freq_bins_html=freq_bins_html,
        consistency_notes_html=consistency_notes_html,
        consistency_summary_html=consistency_summary_html,
        consistency_figures=consistency_blocks,
        conclusion_html=conclusion_html,
    )
    out = output_dir / "report.html"
    write_text(out, rendered)
    return out


def main() -> None:
    ensure_utf8_stdio()
    p = argparse.ArgumentParser(
        description="Compose directivity report.html (script tables + Agent notes)"
    )
    p.add_argument("--output-dir", required=True)
    p.add_argument("--intro-note", default="")
    p.add_argument("--deltas-note", default="")
    p.add_argument("--consistency-note", default="")
    p.add_argument("--conclusion-note", default="")
    args = p.parse_args()

    path = compose_report_html(
        Path(args.output_dir),
        intro_note=args.intro_note,
        deltas_note=args.deltas_note,
        consistency_note=args.consistency_note,
        conclusion_note=args.conclusion_note,
    )
    print(f"OK wrote {path}")


if __name__ == "__main__":
    main()
