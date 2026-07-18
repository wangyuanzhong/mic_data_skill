# -*- coding: utf-8 -*-
"""Load/save analysis params.json (deterministic handoff; process.md is log only)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_params(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"params file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("params.json must be a JSON object")
    return data


def save_params(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_under_output(
    params: dict[str, Any],
    key: str,
    params_path: Path | None = None,
) -> Path:
    """Resolve process_xlsx / process_md under output_dir (else params.json parent)."""
    raw_out = params.get("output_dir") or ""
    if raw_out:
        output_dir = Path(raw_out)
    elif params_path is not None:
        output_dir = Path(params_path).resolve().parent
    else:
        output_dir = Path(".")
    name = params.get(key) or (
        "process.xlsx" if "xlsx" in key else "process.md"
    )
    path = Path(name)
    if path.is_absolute():
        return path
    return (output_dir / path).resolve()


def patch_process_md_section(md_path: Path, heading: str, body: str) -> None:
    """Replace markdown section starting at `## {heading}` until next `## ` or EOF."""
    if not md_path.is_file():
        raise SystemExit(f"process.md not found: {md_path}")
    text = md_path.read_text(encoding="utf-8")
    needle = f"## {heading}"
    start = text.find(needle)
    if start < 0:
        # append
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + body.rstrip() + "\n"
        md_path.write_text(text, encoding="utf-8")
        return
    rest = text[start + len(needle) :]
    # find next level-2 heading
    next_h = rest.find("\n## ")
    if next_h < 0:
        new_text = text[:start] + body.rstrip() + "\n"
    else:
        new_text = text[:start] + body.rstrip() + "\n" + rest[next_h + 1 :]
    md_path.write_text(new_text, encoding="utf-8")
