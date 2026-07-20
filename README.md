# mic_data_skill

Cursor Agent Skills：麦克风 / 音箱等电声产品的**频响（FR）曲线金标分析**与**正式测量报告（PDF）**。

面向电声工程师日常用 Cursor 跑分析；仓库里是 Skill 文档、确定性脚本与设计笔记，不是 Web 应用。

## 包含的 Skill

| Skill | 作用 |
|-------|------|
| [fr-curve-golden-analysis](.cursor/skills/fr-curve-golden-analysis/SKILL.md) | 测量文件夹 → 探查、标准化、灵敏度/曲线金标与过程记录 |
| [fr-curve-measurement-report](.cursor/skills/fr-curve-measurement-report/SKILL.md) | 已有 `params.json` + `process.xlsx` → 出图并生成 `report.html` / `report.pdf` |
| [fr-curve-directivity-analysis](.cursor/skills/fr-curve-directivity-analysis/SKILL.md) | 多角度频响（文件名区分角度）→ 角向−轴向差值、同角度一致性、走势分类、本 Skill 内正式报告 |

入口说明见 [.cursor/skills/README.md](.cursor/skills/README.md)。

## 环境要求

- Python 3.10+（建议 3.12）
- Windows / macOS / Linux 均可；Windows 上组版报告（`fr-curve-measurement-report` 与 `fr-curve-directivity-analysis` 均支持）请用 `--*-note-file` 方式传长文本，避免把引号或长字符串塞进 PowerShell 命令行

## 安装依赖

```bash
pip install -r requirements.txt
# 正式报告 PDF 首次还需要：
playwright install chromium
```

各 Skill 脚本目录下也有一份 `requirements.txt`，与根目录合并内容一致，便于单独拷走 Skill。

## 使用方式

1. 在 Cursor 中打开本仓库（或把 `.cursor/skills/` 拷到你的项目）。
2. 对话里给出测量数据文件夹路径，并说明要「分析 / 选标」或「出报告」。
3. Agent 会按对应 Skill SOP 执行；**产出目录在测量数据文件夹同级**，形如 `<产品>_YYYYMMDD_HHMMSS/`，内含：
   - `params.json`、`process.xlsx`、`process.md`（选标）
   - `figures/`、`report.html`、`report.pdf`（报告）

禁止把分析产出写进本仓库的 `output/`。

## 跑测试

```bash
# 选标侧
pytest .cursor/skills/fr-curve-golden-analysis/scripts/tests -q

# 报告侧
pytest .cursor/skills/fr-curve-measurement-report/scripts/tests -q -m "not integration"

# 指向性侧
pytest .cursor/skills/fr-curve-directivity-analysis/scripts/tests -q

# 跨 Skill 重复脚本一致性
pytest tests/ -q
```

## 文档

设计与实现计划在 [`docs/superpowers/`](docs/superpowers/)。

## 许可

未单独声明许可时，仅供内部 / 协作使用；对外发布前请自行补充 LICENSE。
