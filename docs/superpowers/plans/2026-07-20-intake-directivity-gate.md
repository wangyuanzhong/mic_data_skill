# Intake Confirm + Directivity Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update shared + A/C Skill SOP so Agent forces intake confirmation (including defaults), resolves C intent from @-mention or a yes/no question, and soft-skips C when there is no off-axis data—without changing analysis/plot scripts.

**Architecture:** Add `shared/references/intake-confirm.md` as the single source of truth for the confirmation checklist and intent/skip gates. Wire A and C `SKILL.md` / fill-00 to that file. Extend package `README.md` serial rules. No new params keys for scripts; intent lives in `process.md` / chat only.

**Tech Stack:** Markdown SOP only (Cursor Agent Skills under `.cursor/skills/`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-20-intake-directivity-gate-design.md`
- Do **not** change analysis/plot Python scripts in this plan
- Do **not** add script-read `intent.directivity` to `params.json`
- Except「要不要指向性」, all intake defaults must be shown and **user-confirmed**
- Already @ C → intent=yes, **do not ask** 要不要做指向性
- Not @ C → ask; answer 要 = treat as @ C
- Intent=yes but no off-axis → soft skip C, **do not ask again**
- Same-batch A+B+C: still serial A (then B) complete before writing C wide tables / running C scripts
- A and C output dirs remain physically separate
- Only C (no A): do **not** ask A band 100–15000

---

## File map

| Path | Responsibility |
|------|----------------|
| `shared/references/intake-confirm.md` | **Create** — checklist + intent + soft-skip rules (truth source) |
| `shared/references/fill-00-skeleton.md` | Point to intake-confirm; keep skeleton shape |
| `shared/README.md` | Link new reference |
| `.cursor/skills/README.md` | Serial rule + intake/intent/skip notes |
| `fr-curve-golden-analysis/SKILL.md` | Step 0: confirm pack; ask C intent if not @ C |
| `fr-curve-golden-analysis/references/fill-00-skeleton.md` | Align with shared |
| `fr-curve-directivity-analysis/SKILL.md` | No ask if @/intent yes; soft skip; 1b after off-axis |
| `fr-curve-directivity-analysis/references/fill-00-skeleton.md` | Align with shared |

After repo edits: sync same trees to `C:\Users\zh\.agents\skills\` and `C:\Users\zh\.cursor\skills\` (exclude `_tmp_*`).

---

### Task 1: Create `intake-confirm.md` (truth source)

**Files:**
- Create: `.cursor/skills/shared/references/intake-confirm.md`
- Test: manual read-through against spec §1–§2 (no pytest)

**Interfaces:**
- Produces: document Agent must follow for intake + C intent/skip
- Consumed by: A/C SKILL.md, fill-00, package README (later tasks)

- [ ] **Step 1: Write the full file**

Create `.cursor/skills/shared/references/intake-confirm.md` with **exactly this structure and rules** (Chinese body OK; keep the gate tables):

```markdown
# 开局确认包 + 指向性意向 / 数据能力 Gate

真源：包内 Agent 开局与是否跑 C 的约定。A/C 的 `SKILL.md` 步骤0必须遵守本文；细节版式可再引用 `fill-00-skeleton.md`。

## 意向怎么定

| 情况 | 意向 | 是否问「要不要做指向性」 |
|------|------|--------------------------|
| 已 @ `fr-curve-directivity-analysis`（或用户明确挂载 C） | 要做 | **不问** |
| 未 @ C，开局问后答「要」 | 要做（**视同已 @ C**） | 问 |
| 未 @ C，开局问后答「不要」 | 不做 | 问 |

## 开局确认包（探查前；缺项不探查、不建分析宽表）

贴给用户时写出默认值，**除「要不要指向性」外均有默认，但必须用户确认**。

| 项 | 默认 | 何时出现 |
|----|------|----------|
| 分析根 | 用户路径 | 始终 |
| 产品名 | 可猜，须确认 | 始终 |
| 说明 | 问要不要加；不要→「无」 | 始终 |
| 幅度单位 | 可猜，须确认 | 始终 |
| 要不要做指向性？ | 无默认（是/否） | **仅当未 @ C** |
| A 曲线频段 | 100–15000 Hz | 本批做选标时（已 @ A 或用户明确要做） |
| C 曲线频段 | 250–20000 Hz | 意向=要做 C |
| C 关注频点 | `[1000]` | 意向=要做 C；可加频点或 `[]` |

只挂 C、不挂 A：出现 C 行与公共项；**不要**出现 A 频段行。

## 探查后（仅意向=要做 C）

- `has_off_axis`：可区分角度数（含轴向）≥ 2。
- `has_off_axis=false`：聊天软提示「本批无离轴，指向性跳过」；不建/不推进 C 产出；**不要再问**是否强行做；继续 A/B（若有）。
- `has_off_axis=true`：贴角度×文件名确认表（见 `fill-angle-file-table.md`）；确认前禁止写 C 宽表、禁止跑 C 脚本。

## 同批串行

同时要 A（及 B）+ C：须 A 全完（含奇异值确认；要报告则 B 全完）后，才允许写 C 宽表 / 跑 C 脚本。开局可先收意向与默认；禁止在等 A 确认的空档建 C 目录或写 C 表。A/C 产出目录物理隔离。

## 日志

意向与「无离轴跳过」写入当时 `process.md` 和/或聊天短结。不要新增脚本必读的 intent 字段。
```

- [ ] **Step 2: Verify against spec**

Open `docs/superpowers/specs/2026-07-20-intake-directivity-gate-design.md` and confirm every decision bullet 1–8 appears in the new file (or is explicitly deferred as out of scope for scripts).

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/shared/references/intake-confirm.md
git commit -m "docs(shared): add intake-confirm gate for directivity intent"
```

---

### Task 2: Wire shared fill-00 + shared README

**Files:**
- Modify: `.cursor/skills/shared/references/fill-00-skeleton.md`
- Modify: `.cursor/skills/shared/README.md`
- Test: grep that both link `intake-confirm.md`

**Interfaces:**
- Consumes: `intake-confirm.md` from Task 1
- Produces: fill-00 points Agents to confirm pack before explore

- [ ] **Step 1: Update fill-00-skeleton.md**

Near the top of `.cursor/skills/shared/references/fill-00-skeleton.md` (after the title / before or inside「公共 intake 项」), add:

```markdown
## 开局确认（强制）

步骤0写文件前：按 [`intake-confirm.md`](intake-confirm.md) 贴确认包并取得用户确认。  
未确认完 → 禁止探查、禁止建分析宽表。意向 / 无离轴软跳过规则以该文件为准。
```

Keep existing public intake table; the two rows「曲线分析下限 Hz：强制不许问」与「曲线分析上限 Hz：强制不许问」contradict `intake-confirm.md`. Replace those two rows (keep two rows, one for 下限, one for 上限) with:

```markdown
| 曲线分析下限 Hz | 写出本 Skill 模板默认，**必须用户确认**（可改）；见 `intake-confirm.md` |
| 曲线分析上限 Hz | 写出本 Skill 模板默认，**必须用户确认**（可改）；见 `intake-confirm.md` |
```

(A and C still use their own numeric defaults in their templates; shared only states the confirm rule.)

- [ ] **Step 2: Update shared/README.md**

In the「谁引用」table, add that A/C use `intake-confirm.md`. In「维护约定」, add one bullet: 改 `intake-confirm.md` 须同步 A/C SKILL 步骤0.

- [ ] **Step 3: Commit**

```bash
git add .cursor/skills/shared/references/fill-00-skeleton.md .cursor/skills/shared/README.md
git commit -m "docs(shared): wire fill-00 skeleton to intake-confirm"
```

---

### Task 3: Package README serial + intake notes

**Files:**
- Modify: `.cursor/skills/README.md`
- Test: read「同批多 Skill 串行铁律」section

**Interfaces:**
- Consumes: rules from `intake-confirm.md`
- Produces: package-level serial + intent notes Agents see first

- [ ] **Step 1: Extend「同批多 Skill 串行铁律」**

After the existing numbered list in `.cursor/skills/README.md`, append:

```markdown
5. **开局意向与默认：** 可按 [`shared/references/intake-confirm.md`](shared/references/intake-confirm.md) 在步骤0先收「要不要 C」与频段/关注频点默认；**写 C 宽表 / 跑 C 脚本**仍必须等 A（及若需要的 B）全部结束后。
6. **未 @ C 但用户说要做指向性：** 视同已挂载 C。
7. **已 @ C：** 不要再问「要不要做指向性」；探查无离轴则软跳过 C（提示一句），不要再问是否强行做。
```

Also fix the package `README.md` 角色与触发表第 22 行的「角向−轴向差值」→「轴向−角向差值」，与边界总表（第 35 行）及当前脚本一致（同一 commit 内一并改）。

- [ ] **Step 2: Commit**

```bash
git add .cursor/skills/README.md
git commit -m "docs(skills): document intake intent and soft-skip in package README"
```

---

### Task 4: Update golden-analysis (A) SOP

**Files:**
- Modify: `.cursor/skills/fr-curve-golden-analysis/SKILL.md` (步骤 0 / 铁律)
- Modify: `.cursor/skills/fr-curve-golden-analysis/references/fill-00-skeleton.md`
- Test: checklist in Step 3

**Interfaces:**
- Consumes: `../../shared/references/intake-confirm.md`
- Produces: A step 0 asks C intent when C not attached; confirms A band

- [ ] **Step 1: Patch A SKILL.md 步骤 0**

In「先收信息」/步骤 0, replace the two rows「曲线分析下限 Hz：强制不许问」与「曲线分析上限 Hz：强制不许问」with confirm-required defaults（保持两行）：下限默认 100、上限默认 15000，各写**必须用户确认**（可改）。

Add bullets:

```markdown
- 开局确认包：按 [`../shared/references/intake-confirm.md`](../shared/references/intake-confirm.md) 执行。
- 若本对话**未**挂载指向性 Skill：必须问「本批要不要做指向性？」；答「要」视同已挂载 C（默认与串行规则见该文件）。
- 若已挂载指向性：不要在此重复问「要不要」；C 默认确认由 C 步骤0 / 同批开局确认包一并处理。
```

In 硬规则: 确认包未齐 → 不进步骤1。

- [ ] **Step 2: Patch A fill-00-skeleton.md**

Point to shared `intake-confirm.md` and shared fill-00; state A defaults `f_lo_hz=100`, `f_hi_hz=15000` must be confirmed (not silent). Specifically change the line「`f_lo_hz=100`, `f_hi_hz=15000`（强制不主动问；用户主动提才改）」→「`f_lo_hz=100`, `f_hi_hz=15000`（**必须用户确认**；可改）」.

- [ ] **Step 3: Manual checklist**

Verify by reading only (no run):

1. Un@ C → A must ask 要不要指向性  
2. A band defaults shown and require confirm  
3. Link to intake-confirm resolves relative to A skill

- [ ] **Step 4: Commit**

```bash
git add .cursor/skills/fr-curve-golden-analysis/SKILL.md .cursor/skills/fr-curve-golden-analysis/references/fill-00-skeleton.md
git commit -m "docs(A): force intake confirm and optional directivity intent question"
```

---

### Task 5: Update directivity-analysis (C) SOP

**Files:**
- Modify: `.cursor/skills/fr-curve-directivity-analysis/SKILL.md`
- Modify: `.cursor/skills/fr-curve-directivity-analysis/references/fill-00-skeleton.md`
- Optionally touch: `references/fill-chat-summary.md` if step0 focus_freqs text still says only「主动问」without confirm-pack—align one sentence to intake-confirm
- Test: checklist in Step 3

**Interfaces:**
- Consumes: `intake-confirm.md`, existing `fill-angle-file-table.md`
- Produces: C does not ask 要不要 when attached; soft-skips without off-axis

- [ ] **Step 1: Patch C SKILL.md Overview + 步骤 0**

Add near Overview / 步骤0:

```markdown
- 已挂载本 Skill（或开局意向=要做）：**不要**再问「要不要做指向性」。
- 开局确认包：公共项 + C 频段默认 250–20000 + `focus_freqs` 默认 `[1000]`，按 [`../shared/references/intake-confirm.md`](../shared/references/intake-confirm.md) **强制确认**。
- 同批若还有 A/B：遵守包 README 串行；开局可先确认默认，但写宽表/跑脚本须等 A（及 B）结束。
```

Replace「曲线分析下限/上限：强制不许问」with confirm-required defaults 250/20000（保持下限/上限两行，各写默认 + **必须确认**）。

Also update the `关注频点` row: 把「主动问"要不要加其他频点"」改为确认包式——写出默认 `[1000]`，**必须用户确认**（可加频点或改 `[]`），与 `intake-confirm.md` 一致。

After 步骤1 探查, before 1b:

```markdown
- 若可区分角度（含轴向）< 2：聊天软提示本批无离轴、指向性跳过；**不要再问**；不建/不继续 C 产出（若尚未建则不要建）。本批若有 A/B 则继续它们。
- 若 ≥ 2：进入步骤 1b 角度×文件名确认表。
```

Keep 1b hard rule: no wide table before confirm.

- [ ] **Step 2: Patch C fill-00-skeleton.md**

Same: link intake-confirm; change「`f_lo_hz=250`, `f_hi_hz=20000`（强制不主动问；用户主动提才改）」→「`f_lo_hz=250`, `f_hi_hz=20000`（**必须用户确认**；可改）」; note soft-skip（无离轴时软跳过 C，不二次询问）.

- [ ] **Step 3: Manual checklist**

1. @ C → no 要不要 question in step 0 text  
2. No off-axis → soft skip, no second ask  
3. focus_freqs still default `[1000]` with confirm  
4. Serial pointer to package README present  

- [ ] **Step 4: Commit**

```bash
git add .cursor/skills/fr-curve-directivity-analysis/SKILL.md .cursor/skills/fr-curve-directivity-analysis/references/fill-00-skeleton.md
git commit -m "docs(C): intake confirm, no intent ask when attached, soft-skip without off-axis"
```

---

### Task 6: Sync global skills + acceptance scenarios

**Files:**
- Sync: `C:\Users\zh\.agents\skills\` and `C:\Users\zh\.cursor\skills\` for `shared`, `fr-curve-golden-analysis`, `fr-curve-directivity-analysis`, package `README.md`
- Test: acceptance scenarios below

**Interfaces:**
- Consumes: all Task 1–5 outputs

- [ ] **Step 1: Mirror to global dirs**

```powershell
$srcRoot = "e:\vibe\mic_data_skill\.cursor\skills"
$dests = @("C:\Users\zh\.agents\skills", "C:\Users\zh\.cursor\skills")
$names = @("shared", "fr-curve-golden-analysis", "fr-curve-directivity-analysis")
foreach ($destRoot in $dests) {
  Copy-Item "$srcRoot\README.md" "$destRoot\README.md" -Force
  foreach ($name in $names) {
    $src = Join-Path $srcRoot $name
    $dst = Join-Path $destRoot $name
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    robocopy $src $dst /E /NFL /NDL /NJH /NJS /nc /ns /np /XD _tmp_review_peaks _tmp_review_peaks2 __pycache__ .pytest_cache /XF *.pyc | Out-Null
  }
}
```

- [ ] **Step 2: Acceptance (read SOP / dry mental run)**

Mark each scenario covered by text in intake-confirm + A/C SKILL:

1. 未 @ C，答不要 → 只 A/B  
2. 未 @ C，答要 → 视同 @ C  
3. 已 @ C，无离轴 → 软跳过，不问  
4. 已 @ C，有离轴，同批 A+B → A→B→C 串行  
5. 只挂 C → 不问 A 频段  

- [ ] **Step 3: Commit sync note only if repo changed; else done**

If only global copies changed, no git commit needed. If any leftover repo tweak:

```bash
git status
# commit only if repo files still dirty
```

---

## Spec coverage self-check

| Spec item | Task |
|-----------|------|
| Confirm pack + defaults must confirm | 1, 2, 4, 5 |
| Un@ ask; 要 ≡ @ C | 1, 4 |
| @ C no ask | 1, 5 |
| Soft skip no second ask | 1, 5 |
| C defaults at intake; angle table after explore | 1, 5 |
| Approach shared + gates | 1–3 |
| Only C: no A band | 1, 5 |
| No script / no intent params key | Global Constraints + Task 1 |
| Serial A then C wide/scripts | 1, 3, 5 |
| Acceptance scenarios | 6 |

## Placeholder scan

None intentional. Commits assume git identity already works in the environment (use env `GIT_AUTHOR_*` if needed; do not `git config`).

---
