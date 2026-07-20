# Low/Very-Low Risk Skill Package Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 16 items marked 极低/低 risk in `docs/superpowers/specs/2026-07-20-skills-package-19-issues-risk.md` (items 1,2,3,4,5,6,7,8,9,11,13,14,15,17,18,19), leaving the three 中风险 items (10, 12, 16) untouched for a separate PR.

**Architecture:** Mechanical doc/link/dependency fixes first (fast, zero-judgment), then quality-assurance additions (tests, CI, eval framework), then packaging/format items (frontmatter, license, validate), in an order where later items can rely on earlier ones (e.g. CI needs items 1+2 fixed first; validate needs item 11's frontmatter fields in place).

**Tech Stack:** Python 3.12, pytest, openpyxl, GitHub Actions, `skills-ref` (npx), Cursor Agent Skills.

## Global Constraints

- License stance: internal/private use only (`Proprietary`), no OSS license text to invent.
- Bug-fix policy while adding A's tests (item 7): if a real bug is found only in a `scripts/*.py` file, fix it inline as part of this PR. If fixing requires changing `SKILL.md`/SOP semantics, do NOT change the SOP — log the finding in the final report to the user, unless the SOP wording is a trivial typo/broken-link-class issue.
- Item 6 and item 8 use the "bigger effort" option per user decision: item 6 = actually add `--*-note-file` args to C's `compose_html.py` (not just doc alignment); item 8 = actually add parity tests (not just a doc note).
- Item 13 (eval) is done "fully": real `evals/evals.json` per skill + an actual subagent-run trigger check with genuine evidence recorded, not fabricated. Given cost/time, "fully" is scoped to a representative real pilot (documented honestly), not the full 60-invocation statistical matrix from the official methodology.
- Do not touch items 10, 12, 16 (中风险) in this pass.
- One commit per logical change; verify via pytest / link-check / skills-ref validate before considering a task done.

---

### Task 1: Fix B's test collection (item 1)

**Files:**
- Modify: `.cursor/skills/fr-curve-measurement-report/scripts/tests/conftest.py` (top of file)

**Step:** Add before other imports, mirroring C's conftest:
```python
import sys
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
```
(insert after `from pathlib import Path`, before other local imports)

**Verify:** `pytest .cursor/skills/fr-curve-measurement-report/scripts/tests -q -m "not integration"` from repo root passes.

**Commit:** `fix(B): make report skill tests importable from repo root`

---

### Task 2: Root requirements (item 2)

**Files:**
- Modify: `requirements.txt`

**Step:** Add `numpy>=1.24` and `scipy>=1.11` lines; update header comment from "both FR skills" to "all FR skills" (ties into item 5's wording fix, done together here since it's the same file).

**Verify:** fresh venv install + `import numpy, scipy` + full C test suite passes.

**Commit:** `fix: add numpy/scipy to root requirements for directivity skill`

---

### Task 3 + 4: Broken links (items 3, 4)

**Files:**
- Modify: `.cursor/skills/README.md` (fix `data-contract-sensitivity.md` → `data-contract-sheets-sensitivity.md`)
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md` (remove `http://process.md` fake link, keep plain text `process.md`)

**Verify:** re-run the repo-wide markdown link checker (inline python one-liner used in the earlier audit) — 0 broken links.

**Commit:** `docs: fix broken links in package README and skill A SKILL.md`

---

### Task 5: Root README completeness (item 5)

**Files:**
- Modify: `README.md`

**Step:** Add C (`fr-curve-directivity-analysis`) to the Skill table; add its pytest command to "跑测试"; already handled the "both/all skills" wording in Task 2's requirements.txt, mirror same wording fix here.

**Verify:** all three pytest commands in README actually run and pass.

**Commit:** `docs: add directivity skill to root README skill table and test commands`

---

### Task 6: `--*-note-file` parity for C (item 6, bigger-effort option)

**Files:**
- Modify: `.cursor/skills/fr-curve-directivity-analysis/scripts/compose_html.py`
- Modify: `.cursor/skills/fr-curve-directivity-analysis/scripts/tests/test_compose_smoke.py` (or new test file)
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md` (step 4.3 — mention `--*-note-file` as Windows-safe alternative)
- Modify: `.cursor/skills/fr-curve-measurement-report/SKILL.md` (step 3.2 — document the already-implemented `--*-note-file`, currently undocumented)
- Modify: `README.md` (root) — align the "Windows 用 `--*-file` 方式" claim with reality (now true for both B and C)

**Step 1 (TDD):** Write failing test asserting `compose_html.py --intro-note-file <path>` produces the same `report_sections/intro_note.txt` content as `--intro-note "<same text>"`, for all five C note slots (`intro`, `deltas`, `consistency`, `trend`, `conclusion`).

**Step 2:** In C's `compose_html.py`, mirror B's `_resolve_note` pattern: add `--intro-note-file`, `--deltas-note-file`, `--consistency-note-file`, `--trend-note-file`, `--conclusion-note-file` args; each resolves via file-read when set, else falls back to the existing inline arg. Reuse B's `load_section_html` logic (small enough to inline in C rather than cross-import, keeping C self-contained).

**Verify:** new tests pass; existing C test suite (64 cases) still passes; a manual compose run with a `--intro-note-file` pointing at a UTF-8 file with Chinese text round-trips correctly.

**Commit:** `feat(C): add --*-note-file args matching report skill's Windows-safe pattern`

---

### Task 7: Tests for A's `run_curves.py` / `run_sensitivity.py` / `params_io.py` (item 7)

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/conftest.py` (synthetic `curves` sheet + `process.md` skeleton builder, modeled on C's conftest style)
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_run_sensitivity.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_run_curves.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_params_io.py`

**Coverage (run_sensitivity.py):**
- `midline_mode="mean"` computes mean of 1000Hz-nearest levels correctly; golden = sample closest to midline.
- `midline_mode="value"` uses provided `midline_db`; missing `midline_db` raises `SystemExit`.
- Bin index sign/edges at exact 0.5 dB boundaries (`_bin_index`).
- `sensitivity`/`sensitivity_meta` sheets get written with expected columns; `process.md` `## 灵敏度分析` section gets patched.

**Coverage (run_curves.py):**
- `curves.exclude=None` (pending) → `outlier_gate=pending`, no rank sheets written, `curve_rank`/`outlier_decision` absent.
- `curves.exclude=[]` (confirmed, none excluded) → `outlier_gate=confirmed`, rank/decision sheets present, golden = sample with tightest δ.
- `curves.exclude=["X"]` → excluded sample is absent from `mean_after`/rank, but still traceable in `curve_step3_dev`.
- `aux_count` controls how many rows get `role=aux` in `curve_rank`.
- Unknown name in exclude list raises `SystemExit`.
- High-Q exempt sample nominated but not force-excluded (integration with existing `outliers.py`, reusing fixtures from `test_outliers.py` patterns).

**Coverage (params_io.py):**
- `resolve_under_output` resolves relative vs absolute `process_xlsx`/`process_md` correctly against `output_dir` and against params.json's own parent when `output_dir` is empty.
- `patch_process_md_section` replaces an existing `## heading` section without touching sibling sections, and appends a new section when the heading doesn't exist yet.

**Step 1 (TDD):** Write each test against current behavior (RED if the described behavior isn't yet true — verifies test correctness before checking real behavior).
**Step 2:** Run tests; if any fail because of an actual bug in `run_curves.py`/`run_sensitivity.py`/`params_io.py` (not because of a wrong test expectation), fix the script per Global Constraints bug-fix policy; document any fix in a "bugs found" note added to the final report.

**Verify:** `pytest .cursor/skills/fr-curve-golden-analysis/scripts/tests -q` — all green, meaningful coverage of both scripts' branches.

**Commit(s):** `test(A): add fixtures and coverage for run_sensitivity, run_curves, params_io` (+ separate `fix(A): ...` commit per bug found, if any).

---

### Task 8: Equivalence/divergence documentation + parity tests for duplicated scripts (item 8, bigger-effort option)

**Files:**
- Create: `.cursor/skills/README.md` — add a "重复脚本维护约定" section listing:
  - Equivalence group (must stay behaviorally identical): `compose_pdf.py` (B/C), `quantize.py` (B/C), `params_io.py` (A/C).
  - Intentional divergence: `plot_style.py` (C has directivity-specific helpers B doesn't need; both share the same axis-drawing core functions).
- Create: `.cursor/skills/fr-curve-measurement-report/scripts/tests/test_parity.py` (or a repo-level `scripts/tests/`) comparing shared function behavior across the two copies for the equivalence group.

**Step:** For each equivalence-group file pair, import both copies (by path) into a test and assert identical output for the same input (e.g. `quantize()` on the same float list; `compose_pdf.load_report_html` behavior via a smoke fixture; `params_io.resolve_under_output`/`patch_process_md_section` given the same params dict).

**Verify:** parity tests pass now (they should, since current logic is equivalent — only comments differ); they'll catch future silent drift.

**Commit:** `test: add cross-skill parity tests for scripts intended to stay equivalent` + `docs: document equivalence/divergence groups for duplicated scripts`

---

### Task 9: CI (item 9)

**Files:**
- Create: `.github/workflows/tests.yml`

**Step:** Minimal workflow: on push/PR to any branch, checkout, setup-python 3.12, `pip install -r requirements.txt`, then three steps:
```yaml
- run: pytest .cursor/skills/fr-curve-golden-analysis/scripts/tests -q
- run: pytest .cursor/skills/fr-curve-measurement-report/scripts/tests -q -m "not integration"
- run: pytest .cursor/skills/fr-curve-directivity-analysis/scripts/tests -q
```

**Verify:** YAML validates (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/tests.yml'))"`); cannot fully dry-run GitHub Actions locally, so validate syntax + confirm the exact same three commands pass locally right before committing.

**Commit:** `ci: add GitHub Actions workflow running all three skills' test suites`

---

### Task 11: `compatibility` frontmatter field (item 11)

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md` frontmatter
- Modify: `.cursor/skills/fr-curve-measurement-report/SKILL.md` frontmatter
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md` frontmatter

**Step:** Add `compatibility:` (≤500 chars) per spec:
- A: `Requires Python 3.10+ with openpyxl. Reads/writes an analysis output directory sibling to the measurement data folder.`
- B: `Requires Python 3.10+ with openpyxl, matplotlib, jinja2, playwright (chromium installed via 'playwright install chromium') for PDF generation.`
- C: `Requires Python 3.10+ with openpyxl, matplotlib, jinja2, numpy, scipy, playwright (chromium) for PDF generation.`

**Verify:** run `npx skills-ref@0.1.5 validate <skill_path>` for all three (also covers item 18) — must pass.

**Commit:** `docs: add compatibility field to all three SKILL.md frontmatters`

---

### Task 17: License (item 17, internal/private)

**Files:**
- Create: `LICENSE` (short internal-use notice, no OSS license text)
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md`, `fr-curve-measurement-report/SKILL.md`, `fr-curve-directivity-analysis/SKILL.md` frontmatter — add `license: Proprietary`
- Modify: `README.md` — update "## 许可" section to reference `LICENSE` instead of "未单独声明许可时…"

**Step:** `LICENSE` content: plain statement that this repository and its Skills are for internal/private use only, not licensed for external redistribution, contact repo owner for other uses. No invented legal boilerplate.

**Verify:** `skills-ref validate` still passes (license field is a plain string, no format constraint beyond length).

**Commit:** `docs: mark package as internal/private use with license field and LICENSE file`

---

### Task 14: Fix `^` continuation examples (item 14)

**Files:**
- Modify: `.cursor/skills/fr-curve-measurement-report/SKILL.md` (compose_html multi-line example)
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md` (compose_html multi-line example)

**Step:** Replace the `^`-continued multi-line command blocks with single-line commands (all args on one line — long lines are fine for an Agent to execute, they just aren't readable to a human squinting at markdown, which is an acceptable trade for cross-platform correctness).

**Verify:** commands parse correctly when pasted into both `bash` and PowerShell without modification (visually confirm no `^`/`\` continuation chars remain; the example must be one physical line).

**Commit:** `docs: replace Windows-only ^ line continuation with single-line commands`

---

### Task 15: Unify A/C script path phrasing with B (item 15)

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md` (step 3.1–3.3 command blocks)
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md` (step 3.1–3.8, 4.1, 4.3, 4.4 command blocks)

**Step:** Add the same "本 Skill 根目录 = 本 SKILL.md 所在文件夹" framing B already has, then rewrite each `python .cursor/skills/<name>/scripts/...` command to `python <本Skill根目录>/scripts/...`, matching B's phrasing exactly.

**Verify:** re-read each modified command block; confirm the paths are internally consistent with the new framing sentence.

**Commit:** `docs: unify A/C script invocation phrasing with report skill's portable path convention`

---

### Task 18: Run `skills-ref validate` (item 18)

**Files:** none (verification-only task; may produce fixes if validate fails)

**Step:** `npx --yes skills-ref@0.1.5 validate .cursor/skills/fr-curve-golden-analysis`, same for the other two. Fix any reported violations (most likely already resolved by Task 11's frontmatter additions).

**Verify:** all three return success/no errors.

**Commit:** (folded into Task 11's commit if no separate fixes needed; otherwise its own `fix(skills): resolve skills-ref validate findings`)

---

### Task 19: Mark old gap-analysis doc as superseded (item 19)

**Files:**
- Modify: `docs/superpowers/specs/2026-07-17-mic-fr-skills-package-gap-analysis.md` (add banner at top)

**Step:** Insert immediately after the title:
```markdown
> **superseded:** see [`2026-07-20-skills-package-19-issues-risk.md`](2026-07-20-skills-package-19-issues-risk.md) for the current audit. This document is kept for history; its "C not yet built" / "package README stale" findings are resolved.
```

**Verify:** link resolves (relative, same directory).

**Commit:** `docs: mark 2026-07-17 gap analysis as superseded by the 2026-07-20 audit`

---

### Task 13: Agent-level eval framework + real trigger pilot (item 13, done fully within a scoped real pilot)

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/evals/evals.json`
- Create: `.cursor/skills/fr-curve-measurement-report/evals/evals.json`
- Create: `.cursor/skills/fr-curve-directivity-analysis/evals/evals.json`
- Create: `.cursor/skills/README.md` addendum — "如何跑 eval" pointer section
- Create: `docs/superpowers/specs/2026-07-20-skill-trigger-eval-pilot-results.md` — records the real pilot run: exact queries, dispatch method, observed outcomes, evidence quotes, honest caveats about what wasn't covered.

**Step 1:** For each skill, write 6-8 should-trigger queries (varied phrasing/detail/explicitness) + 4-5 should-not-trigger near-miss queries (including cross-skill near-misses: A vs B vs C are natural near-miss pairs for each other) + `expected_output` descriptions, per the official `evals.json` schema.

**Step 2 (real pilot, not fabricated):** Dispatch `generalPurpose` subagents (fresh context each) with prompts framed as "You are working in this repository as a Cursor agent. A user says: '<query>'. Before doing anything else, state which file(s) under `.cursor/skills/` you would open/consult, if any, and why." for a representative subset (not the full 60-invocation matrix — document this scoping decision). Record actual subagent responses as evidence in the results doc.

**Step 3:** Grade each result against `should_trigger` — did the subagent name the correct skill's SKILL.md path? Record pass/fail with the quoted evidence, per official grading principles (concrete evidence required, no benefit of the doubt).

**Caveat to document honestly:** this proxies Cursor's actual autonomous skill-loading heuristic via subagent reasoning, not a literal capture of Cursor's internal trigger decision — the results doc must say so plainly, per verification-before-completion (no overclaiming).

**Commit:** `test: add agent-level eval scaffolding and record a real trigger-eval pilot`

---

## Execution Status (2026-07-20)

All tasks 1–9, 11, 13–15, 17–19 completed on branch `cursor/skills-low-risk-fixes-fafc`. Verified: fresh-venv install + all four pytest suites (A/B/C/cross-skill parity) green, zero broken links in `.cursor/skills/`, `skills-ref validate` passes for all three skills, CI workflow steps reproduced locally before commit, and a real (scoped) trigger-eval pilot recorded in `docs/superpowers/specs/2026-07-20-skill-trigger-eval-pilot-results.md` (9/9 pass). No real bugs were found in `run_curves.py`/`run_sensitivity.py`/`params_io.py` while adding Task 7's tests — all initial test failures traced back to test-design assumptions, not script defects; details in the final report to the user.

## Self-Review Notes

- Task 2 and Task 5 both touch wording in different files (`requirements.txt` vs `README.md`) — kept as separate commits since they're different files, but bundled conceptually since they fix the same "both/all skills" inconsistency.
- Task 11 and Task 18 are sequenced together (11 before 18) since 18 validates what 11 produces.
- Tasks 1–5, 14, 15, 17, 19 have no cross-task dependencies and could be done in any order; Task 9 (CI) strictly depends on Tasks 1+2 (else CI's first run is red); Task 13 is independent and placed last because it's the most open-ended/time-consuming.
