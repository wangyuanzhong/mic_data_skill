# -*- coding: utf-8 -*-
"""Compose report.html from figure directory + HTML section slots."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sensitivity_tables import sensitivity_bin_count_html

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
        return Path(file_path).read_text(encoding="utf-8")
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


def compose_report_html(
    output_dir: Path,
    *,
    intro_html: str,
    sensitivity_html: str,
    curves_notes_html: str,
    conclusion_html: str,
    figures_dir: Path | None = None,
) -> Path:
    output_dir = Path(output_dir)
    figures_dir = Path(figures_dir) if figures_dir else output_dir / "figures"
    params = {}
    params_path = output_dir / "params.json"
    if params_path.is_file():
        params = json.loads(params_path.read_text(encoding="utf-8"))

    fig_paths = list_figures_in_report_order(figures_dir)
    note_path = figures_dir / "批量一致性说明.txt"
    consistency_note = ""
    if note_path.is_file():
        consistency_note = note_path.read_text(encoding="utf-8").strip()

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

    count_html = sensitivity_bin_count_html(output_dir)
    sensitivity_full = sensitivity_html
    if count_html:
        sensitivity_full = (sensitivity_html or "") + "\n" + count_html

    tpl_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    css = (tpl_dir / "report.css").read_text(encoding="utf-8")
    html = env.get_template("report.html.j2").render(
        product=params.get("product") or "频响测量报告",
        css=css,
        intro_html=intro_html,
        sensitivity_html=sensitivity_full,
        curves_notes_html=curves_notes_html,
        conclusion_html=conclusion_html,
        figures=figure_blocks,
    )
    out = output_dir / "report.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Compose report.html")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--intro", default="<p></p>")
    p.add_argument("--intro-file", default=None)
    p.add_argument("--sensitivity", default="<p></p>")
    p.add_argument("--sensitivity-file", default=None)
    p.add_argument("--curves-notes", default="")
    p.add_argument("--curves-notes-file", default=None)
    p.add_argument("--conclusion", default="<p></p>")
    p.add_argument("--conclusion-file", default=None)
    args = p.parse_args()
    path = compose_report_html(
        Path(args.output_dir),
        intro_html=load_section_html(inline=args.intro, file_path=args.intro_file),
        sensitivity_html=load_section_html(
            inline=args.sensitivity, file_path=args.sensitivity_file
        ),
        curves_notes_html=load_section_html(
            inline=args.curves_notes, file_path=args.curves_notes_file
        ),
        conclusion_html=load_section_html(
            inline=args.conclusion, file_path=args.conclusion_file
        ),
    )
    print(f"OK wrote {path}")


if __name__ == "__main__":
    main()
