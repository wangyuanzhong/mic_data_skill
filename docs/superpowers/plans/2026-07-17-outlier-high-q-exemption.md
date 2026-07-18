# 奇异值 + 高Q豁免 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or subagent-driven-development) to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 在曲线分析中补上「全集均值 → 奇异值提名（Q≥10 豁免）→ 用户确认剔除 → 重算均值 → 排名」，并把每一步详细写入 `process.xlsx` 与 `process.md`。

**Architecture:** 纯函数放 `outliers.py`（估 Q、提名）；`run_curves.py` 两阶段 CLI（未确认 / 已确认 `--exclude`）；Skill 步骤3加门禁并规定 md 填空版式。

**Tech Stack:** Python 3、openpyxl、pytest

## Global Constraints

- Q 阈值固定 **≥ 10**；分析频段默认 100–15000（可用现有 `--f-lo`/`--f-hi`）
- 提名门槛：max|dev| ≥ max(1.0, 2 × 批次中位数 max|dev|)，且非高Q主导
- 无法稳定估 Q → 不给高Q豁免
- 数字只来自脚本；Agent 不手算
- 本轮不做：session JSON、产出目录复用、SPL 列名改造

---

### Task 1: `outliers.py` + 单测（TDD）

**Files:**
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/outliers.py`
- Create: `.cursor/skills/fr-curve-golden-analysis/scripts/tests/test_outliers.py`

- [ ] Step 1: 写失败测试：窄尖峰 Q≥10 → `exempt_high_q=True` 且不进 suggest；宽带偏高 → suggest
- [ ] Step 2: 跑测确认 RED
- [ ] Step 3: 实现 `estimate_peak_q`、`propose_outliers`
- [ ] Step 4: 绿测

### Task 2: 接入 `run_curves.py` 两阶段 + process sheets

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/scripts/run_curves.py`

Sheets（详细、可追溯）:
- `curve_mean_before_outlier`
- `outlier_review`（每样：max_dev、freq、Q、是否稳定、豁免、门槛、是否建议剔除、理由）
- `outlier_decision`（第二阶段：用户决定、是否进入 mean_after）
- `curve_mean_after_outlier`（仅确认后）
- 正式 `curve_rank` / `curve_step4_envelope`（仅确认后）
- `curve_meta`：gate 状态、exclude 名单、规则参数

CLI:
- 无 `--exclude` → 只提名，`outlier_gate=pending`，不写正式金标排名
- `--exclude none` → 确认不剔除
- `--exclude A,B` → 剔除后排名

- [ ] Step 1: 实现并手工跑通一份最小 xlsx
- [ ] Step 2: 断言第二阶段 sheet 齐全

### Task 3: 更新 Skill + process.md 填空版式

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md`

- [ ] 步骤0骨架加「奇异值分析」章
- [ ] 步骤3：灵敏度 → **奇异值门禁** → 曲线排名；每步立刻改 md
- [ ] 规定 `process.md` 奇异值章表格字段与 xlsx 对齐

### Task 4: 验证

- [ ] pytest 全绿
- [ ] 对现有 `CY001升级款_20260717_114219/process.xlsx` 跑 propose → 检查 review 表
- [ ] 用 `--exclude none` 或实际名单跑通第二阶段
