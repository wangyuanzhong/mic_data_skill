# AGENTS.md

## Cursor Cloud specific instructions

This repo is **not a web app**. It is a collection of Cursor Agent Skills for
frequency-response (FR) curve analysis: deterministic Python CLI scripts under
`.cursor/skills/*/scripts/` plus `pytest` suites. The "application" is those
scripts, which turn measurement data into figures and a report (`report.html` /
`report.pdf`). See `README.md` and each `SKILL.md` for behavior.

### Python environment
- Dependencies live in a virtualenv at `.venv` (gitignored). Activate it before
  running anything: `. .venv/bin/activate`. The startup update script creates it
  and installs deps.
- `numpy` and `scipy` are required by the directivity skill but are **not** in the
  root `requirements.txt` (only in
  `.cursor/skills/fr-curve-directivity-analysis/scripts/requirements.txt`). The
  update script installs them explicitly.

### Running tests (non-obvious)
- The report and directivity test suites import sibling modules by bare name
  (e.g. `from render_figures import ...`), so you **must run pytest from inside
  that skill's `scripts/` directory**, not the repo root. Running the report
  command from the repo root as written in `README.md` fails with
  `ModuleNotFoundError`.
  - Report: `cd .cursor/skills/fr-curve-measurement-report/scripts && python -m pytest tests -q -m "not integration"`
  - Report integration (needs Chromium): same dir, `python -m pytest tests -q -m integration`
  - Directivity: `cd .cursor/skills/fr-curve-directivity-analysis/scripts && python -m pytest tests -q`
- The golden skill has no cross-module imports and runs fine from the repo root:
  `pytest .cursor/skills/fr-curve-golden-analysis/scripts/tests -q`.
- There is no configured linter/formatter (no ruff/flake8/pyproject) and no
  pre-commit hooks. `pytest` is the only automated check.

### Report figures / PDF (non-obvious)
- Figure labels and report text are in Chinese. matplotlib needs a CJK font
  (e.g. the `fonts-noto-cjk` system package) or it renders tofu boxes and emits
  "Glyph ... missing from font" warnings. This is a system font package, not a
  pip dependency, so it is not in the update script.
- `report.pdf` is produced with Playwright Chromium (`compose_pdf.py`). Headless
  Chromium works in this VM without extra system libraries. Run
  `playwright install chromium` once (the update script does this).
- Do **not** write analysis outputs into this repo. Skills write to a
  `<product>_YYYYMMDD_HHMMSS/` directory alongside the input data folder; tests
  use temp dirs.
