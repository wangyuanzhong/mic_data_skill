# -*- coding: utf-8 -*-
"""Parity checks for scripts duplicated across skills (per package README's
"重复脚本维护约定"). These load both copies of each file *by path* (not by
package import, since each skill is meant to stay independently copyable)
and assert their public behavior is identical for the same input.

If a change intentionally diverges one copy from the other, update this
file's expectations *and* the equivalence-group note in
`.cursor/skills/README.md` in the same commit.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
A = REPO_ROOT / ".cursor/skills/fr-curve-golden-analysis/scripts"
B = REPO_ROOT / ".cursor/skills/fr-curve-measurement-report/scripts"
C = REPO_ROOT / ".cursor/skills/fr-curve-directivity-analysis/scripts"


def _load(path: Path, unique_name: str) -> ModuleType:
    """Load a script by path, with its own directory temporarily first on
    sys.path so its same-directory imports (e.g. utf8_boot) resolve."""
    scripts_dir = str(path.parent)
    sys.path.insert(0, scripts_dir)
    try:
        spec = importlib.util.spec_from_file_location(unique_name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(scripts_dir)


def test_quantize_b_and_c_are_equivalent():
    b = _load(B / "quantize.py", "parity_quantize_b")
    c = _load(C / "quantize.py", "parity_quantize_c")

    cases = [1.234, -1.25, 0.0, None, "", 100.05, -0.049]
    assert [b.q1(v) for v in cases] == [c.q1(v) for v in cases]
    assert b.q1_list(cases) == c.q1_list(cases)


def test_compose_pdf_load_report_html_signature_equivalent(tmp_path):
    b = _load(B / "compose_pdf.py", "parity_compose_pdf_b")
    c = _load(C / "compose_pdf.py", "parity_compose_pdf_c")

    missing = tmp_path / "does_not_exist.html"
    for mod in (b, c):
        try:
            mod.load_report_html(page=None, html_path=missing)
        except FileNotFoundError:
            continue
        raise AssertionError(f"{mod.__name__} did not raise FileNotFoundError for missing html")

    html = tmp_path / "report.html"
    html.write_text("<html></html>", encoding="utf-8")

    class _FakePage:
        def __init__(self):
            self.goto_calls: list[tuple[str, dict]] = []

        def goto(self, url, **kwargs):
            self.goto_calls.append((url, kwargs))

    page_b, page_c = _FakePage(), _FakePage()
    b.load_report_html(page_b, html)
    c.load_report_html(page_c, html)
    assert page_b.goto_calls == page_c.goto_calls


def test_params_io_a_and_c_are_equivalent(tmp_path):
    a = _load(A / "params_io.py", "parity_params_io_a")
    c = _load(C / "params_io.py", "parity_params_io_c")

    out_dir = tmp_path / "产品_20260101_000000"
    out_dir.mkdir()
    params = {"output_dir": str(out_dir), "process_xlsx": "process.xlsx"}
    assert a.resolve_under_output(params, "process_xlsx") == c.resolve_under_output(
        params, "process_xlsx"
    )

    md = tmp_path / "process.md"
    md.write_text("# 过程记录\n\n## 灵敏度分析\nold\n", encoding="utf-8")
    md_c = tmp_path / "process_c.md"
    md_c.write_text("# 过程记录\n\n## 灵敏度分析\nold\n", encoding="utf-8")

    a.patch_process_md_section(md, "灵敏度分析", "## 灵敏度分析\nnew\n")
    c.patch_process_md_section(md_c, "灵敏度分析", "## 灵敏度分析\nnew\n")
    assert md.read_text(encoding="utf-8") == md_c.read_text(encoding="utf-8")


def test_plot_style_shared_axis_helpers_are_equivalent():
    """plot_style.py intentionally diverges (C has extra smoothing/envelope
    helpers B doesn't need — see README equivalence-group note), but the core
    axis-drawing helpers both skills rely on must stay equivalent."""
    b = _load(B / "plot_style.py", "parity_plot_style_b")
    c = _load(C / "plot_style.py", "parity_plot_style_c")

    for f in (100.0, 1234.0, 20000.0, 999.6):
        assert b.format_hz(f) == c.format_hz(f)

    assert b.octave_centers(100.0, 15000.0) == c.octave_centers(100.0, 15000.0)
    assert b.third_octave_centers(100.0, 15000.0) == c.third_octave_centers(100.0, 15000.0)
