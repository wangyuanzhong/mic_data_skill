# -*- coding: utf-8 -*-
"""Compose report.html from figure directory + Agent notes; tables from scripts."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from section_builders import build_intro_html, build_sensitivity_html, _as_note_html
from utf8_boot import ensure_utf8_stdio, read_text, write_text

ORDER_FIXED_BEFORE_BINS = [
    "奇异值与剔异前均值.png",
    "归零叠图.png",
]
ORDER_FIXED_AFTER_BINS = [
    "金标绝对与偏差.png",
    "辅标偏差叠图.png",
    "辅标绝对叠图.png",
    "批量一致性sigma.png",
]

_BIN_RE = re.compile(r"^包络分档_正负([0-9.]+)dB\.png$")


def load_section_html(*, inline: str, file_path: str | Path | None) -> str:
    """Prefer file contents when file_path is set; else use inline string."""
    if file_path:
        return read_text(file_path)
    return inline


def list_figures_in_report_order(figures_dir: Path) -> list[Path]:
    figures_dir = Path(figures_dir)
    existing = {p.name: p for p in figures_dir.glob("*.png")}
    ordered: list[Path] = []
    for name in ORDER_FIXED_BEFORE_BINS:
        if name in existing:
            ordered.append(existing[name])
    bins: list[tuple[float, Path]] = []
    for name, path in existing.items():
        m = _BIN_RE.match(name)
        if m:
            bins.append((float(m.group(1)), path))
    for _, path in sorted(bins, key=lambda t: t[0]):
        ordered.append(path)
    for name in ORDER_FIXED_AFTER_BINS:
        if name in existing:
            ordered.append(existing[name])
    return ordered


def write_note_files(
    output_dir: Path,
    *,
    intro_note: str = "",
    sensitivity_note: str = "",
    curves_notes: str = "",
    conclusion_note: str = "",
) -> Path:
    """Persist the four note slots under report_sections/ (script-owned files)."""
    sec = Path(output_dir) / "report_sections"
    sec.mkdir(parents=True, exist_ok=True)
    mapping = {
        "intro_note.txt": intro_note or "",
        "sensitivity_note.txt": sensitivity_note or "",
        "curves_notes.txt": curves_notes or "",
        "conclusion_note.txt": conclusion_note or "",
    }
    for name, text in mapping.items():
        write_text(sec / name, text if text.endswith("\n") or text == "" else text + "\n")
    return sec


def compose_report_html(
    output_dir: Path,
    *,
    intro_note: str = "",
    sensitivity_note: str = "",
    curves_notes: str = "",
    conclusion_note: str = "",
    figures_dir: Path | None = None,
    persist_notes: bool = True,
) -> Path:
    """Build report.html. Tables from params/xlsx; notes are CLI fill-ins (script writes note files)."""
    output_dir = Path(output_dir)
    if persist_notes:
        write_note_files(
            output_dir,
            intro_note=intro_note,
            sensitivity_note=sensitivity_note,
            curves_notes=curves_notes,
            conclusion_note=conclusion_note,
        )
    figures_dir = Path(figures_dir) if figures_dir else output_dir / "figures"
    params: dict = {}
    params_path = output_dir / "params.json"
    if params_path.is_file():
        params = json.loads(read_text(params_path))

    fig_paths = list_figures_in_report_order(figures_dir)
    note_path = figures_dir / "批量一致性说明.txt"
    consistency_note = ""
    if note_path.is_file():
        consistency_note = read_text(note_path).strip()

    figure_blocks = []
    for p in fig_paths:
        rel = Path("figures") / p.name
        caption = p.stem
        block = {"src": rel.as_posix(), "caption": caption, "note_html": ""}
        if p.name == "批量一致性sigma.png" and consistency_note:
            paras = "".join(
                f"<p>{line}</p>" for line in consistency_note.splitlines() if line.strip()
            )
            block["note_html"] = f'<div class="figure-note">{paras}</div>'
        figure_blocks.append(block)

    intro_html = build_intro_html(params, intro_note)
    sensitivity_html = build_sensitivity_html(output_dir, sensitivity_note)
    curves_notes_html = _as_note_html(curves_notes)
    conclusion_html = _as_note_html(conclusion_note) or "<p></p>"

    tpl_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    css = read_text(tpl_dir / "report.css")
    html = env.get_template("report.html.j2").render(
        product=params.get("product") or "频响测量报告",
        css=css,
        intro_html=intro_html,
        sensitivity_html=sensitivity_html,
        curves_notes_html=curves_notes_html,
        conclusion_html=conclusion_html,
        figures=figure_blocks,
    )
    out = output_dir / "report.html"
    write_text(out, html)
    return out


def _resolve_note(inline: str, file_arg: str | None, alias_file: str | None) -> str:
    path = file_arg or alias_file
    return load_section_html(inline=inline, file_path=path)


def main() -> None:
    ensure_utf8_stdio()
    p = argparse.ArgumentParser(
        description="Compose report.html (script tables + Agent notes)"
    )
    p.add_argument("--output-dir", required=True)
    p.add_argument("--intro-note", default="", dest="intro_note")
    p.add_argument("--intro-note-file", default=None)
    p.add_argument("--intro-file", default=None, help="alias of --intro-note-file")
    p.add_argument("--intro", default="", help="alias of --intro-note")
    p.add_argument("--sensitivity-note", default="")
    p.add_argument("--sensitivity-note-file", default=None)
    p.add_argument("--sensitivity-file", default=None, help="alias of --sensitivity-note-file")
    p.add_argument("--sensitivity", default="", help="alias of --sensitivity-note")
    p.add_argument("--curves-notes", default="")
    p.add_argument("--curves-notes-file", default=None)
    p.add_argument("--conclusion-note", default="")
    p.add_argument("--conclusion-note-file", default=None)
    p.add_argument("--conclusion-file", default=None, help="alias of --conclusion-note-file")
    p.add_argument("--conclusion", default="", help="alias of --conclusion-note")
    args = p.parse_args()

    intro_inline = args.intro_note or args.intro
    sens_inline = args.sensitivity_note or args.sensitivity
    concl_inline = args.conclusion_note or args.conclusion

    path = compose_report_html(
        Path(args.output_dir),
        intro_note=_resolve_note(
            intro_inline, args.intro_note_file, args.intro_file
        ),
        sensitivity_note=_resolve_note(
            sens_inline, args.sensitivity_note_file, args.sensitivity_file
        ),
        curves_notes=_resolve_note(
            args.curves_notes, args.curves_notes_file, None
        ),
        conclusion_note=_resolve_note(
            concl_inline, args.conclusion_note_file, args.conclusion_file
        ),
    )
    print(f"OK wrote {path}")


if __name__ == "__main__":
    main()
