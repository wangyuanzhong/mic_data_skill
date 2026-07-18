# FR 分析 Skill 包（本仓库 `.cursor/skills/`）

同主题多个 Skill，靠各自 `description` 触发；**不要**在 A 里嵌套执行整份 B 的 SOP。  
共享约定：产出目录（与分析根**同级**，禁止仓库内 `output/`）下的 `params.json` + `process.xlsx` / `process.md`。

| Skill | 何时用 |
|-------|--------|
| [`fr-curve-golden-analysis`](fr-curve-golden-analysis/SKILL.md) | 测量文件夹 → 探查、标准化、灵敏度/曲线金标与过程记录 |
| [`fr-curve-measurement-report`](fr-curve-measurement-report/SKILL.md) | 已有 process 双文件 → 正式 `report.html` / `report.pdf` + 曲线图 |

后续「指向性分析」宜再增独立 Skill，读取金标结果判新样，仍共用表结构，不并进选标 Skill。
