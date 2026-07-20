# mic-fr Skills 包：相对「最正规完整 Skill」缺口清单

**日期:** 2026-07-17  
**仓库:** `mic_data_skill`  
**包位置:** `.cursor/skills/`  
**对照标准:** [Agent Skills Specification](https://agentskills.io/specification)（agentskills.io）+ Cursor create-skill 约定 + 本包「三 Skill 并列流水线」目标  

**用途:** 后续继续开发时的对照清单。已完成项标 ✅，缺口标 ❌ / ⚠️。完成一项可在本文件勾掉并注明日期。

---

## 0. 一句话结论

- **单 Skill 形态：** 两个已有 Skill（选标 / 报告）在「`SKILL.md` + `scripts/` + `references/`」上已经达标；距离「最正规完整」主要差 **可选 frontmatter、`assets/` 归位、包级索引过时、跨 Skill 契约单一真源**。  
- **三 Skill 包形态：** 第三个 Skill（指向性，见包 README 规划）**尚未创建**；包级流水线文档、共享合同、版本与安装说明不完整。  
- **优先级建议：** 先修包 README / 契约 / frontmatter（低成本），再立第三个 Skill 的 design→plan，最后才考虑独立分发仓与 `assets/` 迁徙。

---

## 1. 目标架构（三 Skill 包）

### 1.1 计划中的三个 Skill

| ID | 目录名（计划） | 角色 | 状态 |
|----|----------------|------|------|
| A | `fr-curve-golden-analysis` | 探查 → 标准化 → 灵敏度/奇异值/曲线金辅标 → `params.json` + `process.xlsx` (+ `process.md` 日志) | ✅ 已有 |
| B | `fr-curve-measurement-report` | 读产出目录 → 出图 → HTML→PDF 正式报告 | ✅ 已有（正文/路径已对齐新设计；包 README 未同步） |
| C | （待定，README 称「指向性分析」） | 读金标结果，判新样 / 指向性；**不并进选标** | ❌ 未建 |

### 1.2 目标目录树（正规包形态）

```text
.cursor/skills/                          # 或未来独立仓根
├── README.md                            # 包索引：流水线、边界、安装、版本
├── LICENSE                              # 可选（对外分发时）
├── shared/                              # 可选：跨 Skill 只读契约（推荐后续）
│   └── references/
│       └── data-contract.md             # 或仍由 A 拥有、B/C 只链
├── fr-curve-golden-analysis/            # Skill A
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/                          # 可选
├── fr-curve-measurement-report/         # Skill B
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/                          # 可选
└── fr-curve-<directivity-or-name>/      # Skill C
    ├── SKILL.md
    ├── scripts/
    ├── references/
    └── assets/
```

**原则（包级铁律）：**

1. 三个 Skill **并列**，靠各自 `description` 触发；**禁止**在 A 的 SOP 里嵌套执行完整 B/C。  
2. **共享的是数据合同与产出目录约定**，不是共享一份巨型 SOP。  
3. 脚本跟所属 Skill；公共文档单一真源（A 或 `shared/`），另两个只相对路径引用。  
4. 路径不假设「仓库根」；产出目录 = 分析根**同级**的 `<产品>_时间/`。

---

## 2. 官方「完整单 Skill」对照清单

依据 agentskills.io：**唯一必填**是 `SKILL.md`（含 `name` + `description`）。下列为「正规完整」常用可选件。

### 2.1 目录与文件

| 项 | 规范含义 | A 选标 | B 报告 | C 指向性 |
|----|----------|--------|--------|----------|
| `SKILL.md` | 必填；目录名 = `name` | ✅ | ✅ | ❌ |
| `scripts/` | 可执行代码 + 依赖说明 | ✅ | ✅ | ❌ |
| `references/` | 按需加载的重文档 | ✅（含 data-contract、fill-*） | ✅（report-outline） | ❌ |
| `assets/` | 模板/静态资源（拷贝填空） | ❌（模板在 references / 无独立 assets） | ⚠️（Jinja/CSS 在 `scripts/templates/`，功能有、命名未对齐规范） | ❌ |
| `examples.md` 或等价 | 用法示例（Cursor create-skill 常提） | ❌ | ❌ | — |
| `scripts/requirements.txt` | 依赖钉死 | ✅ | ✅ | — |
| `scripts/tests/` | 非规范必填；工程加分 | ⚠️ 仅 outliers 等 | ✅ 较全 | — |

### 2.2 `SKILL.md` Frontmatter

| 字段 | 必填? | 规范用途 | A | B | 建议 |
|------|-------|----------|---|---|------|
| `name` | 是 | 与目录名一致 | ✅ | ✅ | 保持 |
| `description` | 是 | **何时用** + 边界（勿写完整 SOP） | ✅ | ✅ | 保持；随行为变更更新触发词 |
| `license` | 否 | 许可证名或文件 | ❌ | ❌ | 对内可写 `Proprietary`；对外再补 LICENSE |
| `compatibility` | 否 | 环境：Python、包、Playwright 等 | ❌ | ❌ | **建议补**（报告尤其需要） |
| `metadata` | 否 | `package` / `version` / `role` / `upstream` | ❌ | ❌ | **建议补**（三 Skill 包识别） |
| `allowed-tools` | 否 | 预批准工具（实验性） | ❌ | ❌ | **暂不写**（支持不稳） |
| Cursor: `disable-model-invocation` | Cursor 扩展 | `true` = 仅显式 @ 加载 | ❌ | ❌ | 按产品策略二选一；默认可省略（允许自动匹配） |

**推荐 frontmatter 模板（后续可直接粘贴改）：**

```yaml
---
name: <skill-dir-name>
description: >-
  Use when <触发场景与关键词>. Do not use for <明确排除>.
license: Proprietary
compatibility: >-
  Requires Python 3.11+ and <deps>. Input/output under sibling analysis output dir.
metadata:
  package: mic-fr-skills
  version: "0.1.0"
  role: analysis | report | directivity
  upstream: fr-curve-golden-analysis   # 仅下游 skill 需要
---
```

### 2.3 正文与渐进披露

| 项 | 规范建议 | A | B |
|----|----------|---|---|
| `SKILL.md` 不宜过长（建议 &lt;500 行 / 指令可控） | 细节进 references | ⚠️ A 的 SKILL 仍较长（SOP 全在正文） | ✅ 相对短 |
| 相对路径引用一层深 | 避免深链 | ✅ 大体一层 | ⚠️ 链到兄弟 skill 的 data-contract（包内可接受，独立拷走 B 会断） |
| description 不摘要完整工作流 | 防 Agent 只读 description | ✅ | ✅ |
| 硬规则 / 闸门写清 | — | ✅ | ✅ |

### 2.4 验证

| 项 | 说明 | 状态 |
|----|------|------|
| `skills-ref validate ./skill` | 官方校验 frontmatter/命名 | ❌ 未纳入开发流程 |
| 压力/场景测（writing-skills TDD） | 纪律类 skill 推荐 | ⚠️ 以脚本单测为主，缺「无 skill 基线 Agent」测试 |

---

## 3. 包级（多 Skill）缺口

### 3.1 包索引 `README.md`

| 项 | 状态 | 说明 |
|----|------|------|
| 存在包 README | ✅ | `.cursor/skills/README.md` |
| 流水线与现状一致 | ❌ | 仍写「process 双文件 → `report.md`」；实际 B 为 **不读 process.md**、产出 **PDF**、输入在分析根**同级** |
| 三 Skill 表 | ⚠️ | 只列 A/B，C 仅一句话 |
| 边界表（谁禁止代劳谁） | ⚠️ | 散落在各 SKILL；包级无总表 |
| 安装依赖 | ❌ | 未写 A/B 的 pip、Playwright chromium |
| 产出目录约定图示 | ⚠️ | A/B SKILL 有；README 未画清 |
| 版本号 / changelog | ❌ | 无包级 version |
| LICENSE | ❌ | 无 |

### 3.2 共享数据契约

| 项 | 状态 | 说明 |
|----|------|------|
| `data-contract.md`（params + sheets） | ✅ 在 A 的 `references/` | 生产者合同正确位置之一 |
| B 只引用、不复制 | ✅ | 相对路径 `../fr-curve-golden-analysis/references/data-contract.md` |
| C 如何引用 | ❌ | C 未建；需预定同一合同 |
| `shared/` 单一真源 | ❌ | 可选重构：合同上移 `shared/references/`，A/B/C 都链过去，避免「只装 B」断链时无文档 |
| 合同与脚本列名持续同步机制 | ⚠️ | 靠人工；无「改脚本必改合同」检查项 |

### 3.3 流水线与触发

| 项 | 状态 |
|----|------|
| A → 产出目录闸门 → B | ✅ 设计已定；B SKILL 已写 |
| A → C（读金标判新样） | ❌ 无 design/SOP |
| C → B 是否出报告 | ❌ 未定义 |
| description 互斥足够清晰 | ⚠️ A/B 已互斥；C 需同样写 Do not use for… |
| 用户只给分析根时如何找产出目录 | ✅ B Overview 已写；README 未同步 |

### 3.4 分发与可移植性

| 项 | 状态 | 说明 |
|----|------|------|
| 可整包拷贝 `.cursor/skills/` | ⚠️ | 兄弟相对路径要求 A+B 同在 |
| 单 Skill 独立分发 | ❌ | B 依赖 A 的 data-contract 路径；脚本路径已改为「本 skill 目录」✅ |
| 独立 Git 仓 `mic-fr-skills` | ❌ | 未拆；非必须 |
| CI：pytest A + pytest B | ❌ | 仅本地可跑 |

---

## 4. 分 Skill 详细缺口

### 4.1 Skill A — `fr-curve-golden-analysis`

**已有：** SOP 完整；`params.json` 真源；脚本灵敏度/曲线；fill 模板；data-contract；与报告边界在 description。

| 缺口 | 优先级 | 备注 |
|------|--------|------|
| 补 `compatibility` / `metadata` / 可选 `license` | P1 | 见 §2.2 |
| `SKILL.md` 过长 → 更多步骤下沉 references | P2 | 渐进披露 |
| `assets/`（若有可拷贝空白模板） | P3 | params 模板已在 references，可保留 |
| 测试覆盖扩大（灵敏度/曲线脚本） | P2 | 现有 outliers 测 |
| 包 README 同步「不做正式 PDF」 | P1 | |
| 合同变更 checklist | P2 | 改 sheet 列必改 data-contract |

### 4.2 Skill B — `fr-curve-measurement-report`

**已有：** SOP；闸门；出图脚本；HTML/PDF 组版；分页硬约束；中文图名；一致性说明 txt；tests。

| 缺口 | 优先级 | 备注 |
|------|--------|------|
| 补 frontmatter 可选字段 | P1 | 尤其 compatibility（Playwright） |
| 包 README 仍写 report.md — **必须改** | P0 | 文档债务 |
| `scripts/templates/` → 是否迁 `assets/` | P3 | 正规命名；非功能阻塞 |
| `examples.md`（一次真实产出目录走通示例，无真实数据进仓） | P2 | 用合成夹具路径说明即可 |
| 端到端真实批次验收清单 | P1 | 合成测已有；缺真实数据手工验收表 |
| description / Overview 与「同级产出目录」 | ✅ | 已改 |
| 改格式只改组版层 | ✅ | 已写 |

### 4.3 Skill C — 指向性（规划名，待定）

| 缺口 | 优先级 | 备注 |
|------|--------|------|
| 正式命名 + 目录 | P0 | 如 `fr-curve-directivity-check` |
| design 文档（输入：金标结果？新样测量？闸门？） | P0 | brainstorm → spec |
| `SKILL.md` + description 互斥 A/B | P0 | |
| 是否写回 process.xlsx 新 sheet / 是否出图 / 是否进 PDF | P0 | 产品决策 |
| scripts + references + tests | P1 | |
| 挂到包 README 流水线 | P0 | |

---

## 5. 与「最正规完整」差距总表（按优先级）

### P0 — 继续开发前建议先做

1. **更新包 `README.md`：** 三 Skill 表、正确流水线（同级产出、`params`+`xlsx`、PDF、不读 md）、边界表、安装命令。  
2. **冻结 Skill C 的产品范围**（输入输出、与 A/B 边界）并开 design。  
3. **确认 data-contract 真源策略**（留在 A vs 上移 `shared/`）。

### P1 — 正规化补强

4. 两 Skill 补齐 `compatibility` + `metadata`（+ 可选 `license`）。  
5. 报告 skill：真实批次手工验收清单（勾选七类图、分页、一致性说明）。  
6. 引入或记录 `skills-ref validate`（有 Node/工具时）。  
7. 合同 ↔ 脚本列名同步约定写入包 README。

### P2 — 体验与质量

8. A 的 SKILL 瘦身（步骤细节下沉）。  
9. A 脚本测试加宽。  
10. B 增加 `examples.md`（合成路径 walkthrough）。  
11. 包级 `version` / 简短 CHANGELOG。

### P3 — 锦上添花

12. `assets/` 目录归位（模板从 `scripts/templates` 迁出）。  
13. 独立分发仓、LICENSE、CI。  
14. `allowed-tools` / `disable-model-invocation` 策略实验。  
15. writing-skills 式 Agent 压力测试（无 skill 基线）。

---

## 6. 建议的后续开发顺序（路线图）

```text
Phase 0  文档对齐
         └─ 改包 README（流水线/边界/安装）← 本缺口清单配套

Phase 1  元数据正规化
         └─ A/B frontmatter：compatibility + metadata (+ license)

Phase 2  契约策略
         └─ 决定 data-contract 留 A 或 shared/；改链接；加「改脚本必改合同」

Phase 3  Skill C
         └─ brainstorm → spec → plan → 实现（并列，不塞进 A）

Phase 4  验收与发布姿态
         └─ 真实数据验收表、skills-ref、可选独立仓/CI/assets 迁徙
```

---

## 7. 包 README 应有的「边界总表」（待写入 README）

| 动作 | A 选标 | B 报告 | C 指向性（计划） |
|------|--------|--------|------------------|
| 探原始测量包 | ✅ | ❌ | ⚠️ 待定（通常只读新样或只读结果） |
| 写/改 `params.json`、分析 sheet | ✅ | ❌ | ⚠️ 待定 |
| 写 `process.md` 过程日志 | ✅ | ❌ | ⚠️ |
| 出正式 `report.pdf` / 报告图 | ❌ | ✅ | ❌（除非明确要求） |
| 读 `process.md` | 过程用 | ❌ | ⚠️ 建议否，与 B 一致吃 xlsx/json |

---

## 8. 当前仓库事实快照（2026-07-17）

```text
.cursor/skills/
├── README.md                          # ⚠️ 内容过时
├── fr-curve-golden-analysis/          # ✅ Skill A
│   ├── SKILL.md                       # 缺可选 YAML
│   ├── references/                    # 含 data-contract.md ✅
│   └── scripts/                       # + 部分 tests
└── fr-curve-measurement-report/       # ✅ Skill B
    ├── SKILL.md                       # 缺可选 YAML；路径/分页已较新
    ├── references/report-outline.md
    └── scripts/                       # 出图+组版+较全 tests；templates 在 scripts 下
```

相关设计/计划文档：

- `docs/superpowers/specs/2026-07-16-fr-curve-golden-analysis-design.md`
- `docs/superpowers/specs/2026-07-17-fr-curve-measurement-report-design.md`
- `docs/superpowers/plans/2026-07-17-fr-curve-measurement-report.md`

---

## 9. 使用方式（给你后续开发）

1. 开新任务时先看 **§5 优先级**，从 P0 勾。  
2. 每完成一项：在本文件对应行改 ✅，并在包 README 或 CHANGELOG 留一行。  
3. 开 Skill C 前：不要先写代码；按 Superpowers：**brainstorming → spec → writing-plans → 实现**。  
4. 任何改动 `process.xlsx` sheet/列：同步 `data-contract.md`，并检查 B（及未来 C）是否依赖该列。

---

## 10. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-17 | 初稿：对照 agentskills.io + 三 Skill 包目标，基于当前仓库盘点 |
| 2026-07-18 | `data-contract.md` 从选标 references **迁至**报告 Skill `references/`（消费者刚需）；包 README 增加维护者同步约定。下文 §3.2 / §8 若仍写「在 A」以本条为准。 |
