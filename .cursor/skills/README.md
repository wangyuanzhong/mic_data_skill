# FR 分析 Skill 包（本仓库 `.cursor/skills/`）

同主题多个 Skill，靠各自 `description` 触发；**不要**在 A 里嵌套执行整份 B/C 的 SOP。  
共享约定：产出目录（与分析根**同级**，禁止仓库内 `output/`）下的 `params.json` + `process.xlsx` / `process.md`。

## 同批多 Skill 串行铁律（禁止并行）

用户**同时**要做选标（A）与指向性（C），或一次挂载多个相关 Skill、或说「分析并出报告」覆盖两者时：

1. **必须严格串行**：先完整跑完 A（步骤 0→3 全闸门，含奇异值用户确认与曲线第二阶段）→ 若还要选标正式报告则再完整跑完 B → **全部结束后**才允许开始 C 步骤 0。
2. **禁止并行 / 穿插**：禁止两边同时建产出目录、同时探查、同时写宽表；禁止 A 卡在「等用户确认」时去推进 C（或反过来）；禁止「一边等确认一边把另一 Skill 跑完」。
3. A 与 C 产出目录仍**物理隔离**（两个 `<产品>_<时间>/`），但这不等于可以并行开工。
4. 仅指向性、或仅选标：按各自 SOP，本条不适用。
5. **开局意向与默认：** 可按 [`shared/references/intake-confirm.md`](shared/references/intake-confirm.md) 在步骤0先收「要不要 C」与频段/关注频点默认；**写 C 宽表 / 跑 C 脚本**仍必须等 A（及若需要的 B）全部结束后。
6. **未 @ C 但用户说要做指向性：** 视同已挂载 C。
7. **已 @ C：** 不要再问「要不要做指向性」；探查无离轴则软跳过 C（提示一句），不要再问是否强行做。

## 角色与触发

| 层 / Skill | 何时用 |
|------------|--------|
| `shared/`（**非触发 Skill**，无 `SKILL.md`） | A/C 通过相对路径引用公共 intake、探查、角度×文件名确认表等约定 |
| [`fr-curve-golden-analysis`](fr-curve-golden-analysis/SKILL.md) | 测量文件夹 → 探查、标准化、灵敏度 / 曲线金标与过程记录 |
| [`fr-curve-measurement-report`](fr-curve-measurement-report/SKILL.md) | 已有选标产出（params + xlsx）→ 正式 `report.html` / `report.pdf` + 曲线图 |
| [`fr-curve-directivity-analysis`](fr-curve-directivity-analysis/SKILL.md) | 多角度频响（文件名区分角度）→ 轴向−角向差值、同角度一致性、本 Skill 内正式报告 |

`shared/` 不是独立 Skill：没有 `description`，不参与触发匹配；只给 A/C 引用。整包安装，不要只拷单个 Skill 却不带 `shared/`。

## 边界总表

| 动作 | shared | A 选标 | B 选标报告 | C 指向性 |
|------|--------|--------|-----------|----------|
| 探原始测量包 | ❌ | ✅ | ❌ | ✅ |
| 写 `params.json` 公共字段 | 提供 base | ✅（+A 专有） | ❌ | ✅（+C 专有） |
| 写 `process.xlsx` 宽表 | ❌ | ✅（单表 `curves`） | ❌ | ✅（一角度一 sheet） |
| 写 `process.md` 过程日志 | ❌ | ✅ | ❌（不读） | ✅ |
| 灵敏度 / 奇异值 / 金辅标 | ❌ | ✅ | ❌ | ❌ |
| 角向−轴向差值 / 同角度一致性 | ❌ | ❌ | ❌ | ✅ |
| 包络合格判定 | ❌ | ❌（A 无） | ❌ | ⚠️ 可选（`envelope` 非空时；本 plan 恒 null） |
| 出正式 `report.html` / `report.pdf` | ❌ | ❌ | ✅（选标产出） | ✅（C 产出，本 Skill 内） |
| 读 `process.md` 当数字真源 | — | 过程用 | ❌ | ❌ |

## 产出目录约定

所有 Skill 的产出目录建在**与分析根同级**（分析根的父目录下），名 `<产品>_<YYYYMMDD_HHMMSS>`；禁止建在仓库/skill 的 `output/`。

A 选标产出与 C 指向性产出**物理隔离**：同一批数据既选标又指向性 = 两个产出目录，各自独立的 `params.json` / `process.xlsx` / `process.md`。

## 给人看的说明（维护者；Agent 跑 SOP 不必读本节）

### 数据合同（按文件拆开，勿合并回单文件）

**A 选标产出**的合同在报告 Skill `references/`：

| 文件 | 内容 |
|------|------|
| [`data-contract-params.md`](fr-curve-measurement-report/references/data-contract-params.md) | `params.json` 字段 |
| [`data-contract-sheets-curves-wide.md`](fr-curve-measurement-report/references/data-contract-sheets-curves-wide.md) | 宽表 `curves` |
| [`data-contract-sheets-sensitivity.md`](fr-curve-measurement-report/references/data-contract-sensitivity.md) | 灵敏度 sheets |
| [`data-contract-sheets-curves.md`](fr-curve-measurement-report/references/data-contract-sheets-curves.md) | 曲线/奇异值 sheets（不含 meta） |
| [`data-contract-curve-meta.md`](fr-curve-measurement-report/references/data-contract-curve-meta.md) | `curve_meta` / `outlier_gate` |
| [`data-contract-report-quickref.md`](fr-curve-measurement-report/references/data-contract-report-quickref.md) | 报告「读哪里」速查 |

选标 Agent 日常不读；报告 Agent **按 SOP 步骤只打开当步需要的那几个文件**。

**C 指向性产出**的合同在 C Skill `references/`：

| 文件 | 内容 |
|------|------|
| [`data-contract-params.md`](fr-curve-directivity-analysis/references/data-contract-params.md) | C `params.json` 字段（含 `angles` / `axial_angle` / `envelope`） |
| [`data-contract-sheets.md`](fr-curve-directivity-analysis/references/data-contract-sheets.md) | 角度宽表 / `delta_*` / `consistency_*` / `consistency_summary` |

### 改脚本列/sheet 时的同步约定

- 改 A 选标脚本若增删/改名 sheet 或列：只改对应那一份 `data-contract-*.md`（如改灵敏度列 → 改 `data-contract-sheets-sensitivity.md`），否则报告会抄错或漏表。
- 改 C 脚本若增删角度相关 sheet 或列：改 C 的 `data-contract-sheets.md`。
- 改 `shared/` 下任何 fill/模板：检查 A/C SOP 是否仍对得上。
- A 的 `params.template.json` 仍基于 `shared/references/params.base.template.json` + A 专有字段；C 同理。

### shared 不是 Skill

`shared/` 目录**没有** `SKILL.md`，不会被 Cursor 当 Skill 加载。若误加 `SKILL.md`，会被 `description` 触发匹配，请删除。
