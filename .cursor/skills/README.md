# FR 分析 Skill 包（本仓库 `.cursor/skills/`）

同主题多个 Skill，靠各自 `description` 触发；**不要**在 A 里嵌套执行整份 B 的 SOP。  
共享约定：产出目录（与分析根**同级**，禁止仓库内 `output/`）下的 `params.json` + `process.xlsx` / `process.md`。

| Skill | 何时用 |
|-------|--------|
| [`fr-curve-golden-analysis`](fr-curve-golden-analysis/SKILL.md) | 测量文件夹 → 探查、标准化、灵敏度/曲线金标与过程记录 |
| [`fr-curve-measurement-report`](fr-curve-measurement-report/SKILL.md) | 已有 process 双文件 → 正式 `report.html` / `report.pdf` + 曲线图 |

后续「指向性分析」宜再增独立 Skill，读取金标结果判新样，仍共用表结构，不并进选标 Skill。

---

## 给人看的说明（维护者；Agent 跑 SOP 不必读本节）

- **数据合同**（按文件拆开，勿合并回单文件）在报告 Skill `references/`：

  | 文件 | 内容 |
  |------|------|
  | [`data-contract-params.md`](fr-curve-measurement-report/references/data-contract-params.md) | `params.json` 字段 |
  | [`data-contract-sheets-curves-wide.md`](fr-curve-measurement-report/references/data-contract-sheets-curves-wide.md) | 宽表 `curves` |
  | [`data-contract-sheets-sensitivity.md`](fr-curve-measurement-report/references/data-contract-sheets-sensitivity.md) | 灵敏度 sheets |
  | [`data-contract-sheets-curves.md`](fr-curve-measurement-report/references/data-contract-sheets-curves.md) | 曲线/奇异值 sheets（不含 meta） |
  | [`data-contract-curve-meta.md`](fr-curve-measurement-report/references/data-contract-curve-meta.md) | `curve_meta` / `outlier_gate` |
  | [`data-contract-report-quickref.md`](fr-curve-measurement-report/references/data-contract-report-quickref.md) | 报告「读哪里」速查 |

  选标 Agent 日常不读；报告 Agent **按 SOP 步骤只打开当步需要的那几个文件**。
- **改选标脚本**若增删/改名 sheet 或列：只改对应那一份 `data-contract-*.md`（例如改灵敏度列 → 改 `data-contract-sheets-sensitivity.md`），否则报告会抄错或漏表。
- 选标侧的 `params.template.json` 仍在分析 Skill `references/`，只用于开工拷贝填空，与合同不是同一文件。
