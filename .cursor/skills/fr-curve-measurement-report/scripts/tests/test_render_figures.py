# -*- coding: utf-8 -*-
from render_figures import render_all_figures


def test_render_creates_core_pngs(synthetic_ready_dir, tmp_path):
    fig_dir = tmp_path / "figures"
    paths = render_all_figures(synthetic_ready_dir, fig_dir)
    names = {p.name for p in paths}
    assert "奇异值与剔异前均值.png" in names
    assert "归零叠图.png" in names
    assert "剔异后归零叠图.png" not in names
    assert "金标绝对与偏差.png" in names
    assert "批量一致性sigma.png" in names
    assert "批量一致性说明.txt" in names
    assert any(n.startswith("包络分档_正负") and n.endswith(".png") for n in names)
    assert all(p.is_file() and p.stat().st_size > 0 for p in paths)
    note = (fig_dir / "批量一致性说明.txt").read_text(encoding="utf-8")
    assert "一致性" in note or "σ" in note
