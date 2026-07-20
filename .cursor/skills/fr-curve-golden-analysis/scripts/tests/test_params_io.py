# -*- coding: utf-8 -*-
"""Tests for params_io: path resolution and process.md section patching."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from params_io import patch_process_md_section, resolve_under_output  # noqa: E402


def test_resolve_under_output_relative_to_output_dir(tmp_path):
    out = tmp_path / "产品_20260101_000000"
    out.mkdir()
    params = {"output_dir": str(out), "process_xlsx": "process.xlsx"}
    resolved = resolve_under_output(params, "process_xlsx")
    assert resolved == (out / "process.xlsx").resolve()


def test_resolve_under_output_absolute_path_passthrough(tmp_path):
    abs_path = tmp_path / "elsewhere" / "custom.xlsx"
    params = {"output_dir": str(tmp_path), "process_xlsx": str(abs_path)}
    resolved = resolve_under_output(params, "process_xlsx")
    assert resolved == abs_path


def test_resolve_under_output_falls_back_to_params_json_parent(tmp_path):
    params_path = tmp_path / "params.json"
    params = {"output_dir": "", "process_md": "process.md"}
    resolved = resolve_under_output(params, "process_md", params_path)
    assert resolved == (tmp_path / "process.md").resolve()


def test_resolve_under_output_default_filename_when_key_missing():
    params = {"output_dir": "/tmp/out"}
    resolved = resolve_under_output(params, "process_xlsx")
    assert resolved.name == "process.xlsx"
    resolved_md = resolve_under_output(params, "process_md")
    assert resolved_md.name == "process.md"


def test_patch_process_md_section_replaces_existing_heading_only(tmp_path):
    md = tmp_path / "process.md"
    md.write_text(
        "\n".join(
            [
                "# 过程记录",
                "",
                "## 灵敏度分析",
                "old sensitivity content",
                "",
                "## 奇异值分析",
                "untouched outlier content",
                "",
            ]
        ),
        encoding="utf-8",
    )
    patch_process_md_section(md, "灵敏度分析", "## 灵敏度分析\n\nnew sensitivity content\n")
    text = md.read_text(encoding="utf-8")
    assert "new sensitivity content" in text
    assert "old sensitivity content" not in text
    assert "untouched outlier content" in text


def test_patch_process_md_section_appends_when_heading_absent(tmp_path):
    md = tmp_path / "process.md"
    md.write_text("# 过程记录\n\nintro line\n", encoding="utf-8")
    patch_process_md_section(md, "曲线分析", "## 曲线分析\n\nnew curves content\n")
    text = md.read_text(encoding="utf-8")
    assert "intro line" in text
    assert "## 曲线分析" in text
    assert "new curves content" in text


def test_patch_process_md_section_missing_file_raises():
    import pytest

    with pytest.raises(SystemExit):
        patch_process_md_section(Path("/nonexistent/process.md"), "灵敏度分析", "body")
