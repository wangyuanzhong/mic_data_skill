# Report compose: script tables + Agent notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement task-by-task.

**Goal:** 报告正文表格与骨架由脚本从 `params.json`/`process.xlsx` 生成；Agent 只提供各节白话填空（note），不再手写 HTML 大表。

**Architecture:** `compose_html` 组装 intro（params 表 + note）与 sensitivity（note + 明细表 + 计数表）；曲线/结论仍为 note + 脚本插图。CLI 改为 `--*-note-file`（保留旧 `--*-file` 作 note 别名以免立刻打碎调用）。

**Tech Stack:** Python、openpyxl、pytest、现有 Jinja 模板

## Global Constraints

- 数字禁止手算；表只来自 sheet/params
- Agent 禁止手写灵敏度明细表 / 介绍字段表
- 改版式仍只动 CSS/j2 + 重跑 compose

---

### Task 1: 灵敏度明细表 HTML（TDD）

**Files:** `sensitivity_tables.py`, `tests/test_sensitivity_tables.py`

- [x] 失败测试：`sensitivity_detail_html` 含样机名与表头
- [x] 实现从 `sensitivity` sheet 生成逐台表
- [x] 绿测

### Task 2: 介绍字段表 + compose 组装（TDD）

**Files:** `section_builders.py`（新建）, `compose_html.py`, `tests/test_compose.py`

- [x] `build_intro_html(params, note)` / `build_sensitivity_html(output_dir, note)`
- [x] `compose_report_html` 用 note 参数；始终追加脚本表
- [x] CLI：`--intro-note-file` 等；旧 `--intro-file` 等同 note
- [x] 测试：仅空 note 也有灵敏度明细 + 计数；介绍含产品名

### Task 3: 更新 Skill / outline

**Files:** `SKILL.md`, `references/report-outline.md`

- [x] SOP：Agent 只写 note 文件；禁止手写表
- [x] 示例命令改 `--*-note-file`

### Task 4: 验证

- [x] `pytest …/scripts/tests -q -m "not integration"`（26 passed）
