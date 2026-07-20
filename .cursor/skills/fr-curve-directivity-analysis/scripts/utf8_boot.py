# -*- coding: utf-8 -*-
"""Force UTF-8 for stdio and text files (Windows GBK safe)."""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def read_text(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: Path | str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8", newline="\n")
