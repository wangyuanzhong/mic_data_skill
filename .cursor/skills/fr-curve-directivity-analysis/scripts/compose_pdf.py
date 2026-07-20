# -*- coding: utf-8 -*-
"""HTML → PDF via Playwright Chromium (UTF-8 safe for Chinese paths)."""
from __future__ import annotations

import argparse
from pathlib import Path

from utf8_boot import ensure_utf8_stdio


def load_report_html(page, html_path: Path) -> None:
    html_path = Path(html_path).resolve()
    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    page.goto(html_path.as_uri(), wait_until="networkidle")


def html_to_pdf(html_path: Path, pdf_path: Path | None = None) -> Path:
    html_path = Path(html_path).resolve()
    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    pdf_path = Path(pdf_path) if pdf_path else html_path.with_suffix(".pdf")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        load_report_html(page, html_path)
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
        )
        browser.close()
    return pdf_path


def main() -> None:
    ensure_utf8_stdio()
    p = argparse.ArgumentParser(description="Render report.html to PDF")
    p.add_argument("--html", required=True)
    p.add_argument("--pdf", default=None)
    args = p.parse_args()
    out = html_to_pdf(Path(args.html), Path(args.pdf) if args.pdf else None)
    print(f"OK wrote {out}")


if __name__ == "__main__":
    main()
