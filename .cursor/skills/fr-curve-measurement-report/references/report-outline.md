# 正式报告正文版式（白话填空说明）

数字与表格由组版脚本从产出目录 `params.json` / `process.xlsx` 生成。  
字段/sheet 含义按需打开同目录 `data-contract-*.md`（总表见 [data-contract-report-quickref.md](data-contract-report-quickref.md)）。  

Agent **只**把白话当作 `compose_html.py` 的命令行参数传入；**不写** `report_sections/`（脚本落盘四个 `.txt`）。

## 传参（对应 compose 参数）

| 参数 | 内容 | 可空 |
|------|------|------|
| `--intro-note` | 介绍一两句 | 可 |
| `--sensitivity-note` | 金标为何选它等 | 可 |
| `--curves-notes` | 曲线/读图短说明 | 可 |
| `--conclusion-note` | 结论三四句 | 建议有 |

纯白话；不要表、不要尖括号标签。

## 脚本生成（Agent 勿重复）

1. **介绍字段表** + intro-note  
2. **灵敏度：** note（若有）→ **灵敏度明细** → **灵敏度分档计数**  
3. **曲线：** curves-notes + 固定顺序插图（奇异值图→归零叠图→包络分档→金标→辅标→一致性；一致性说明贴图下）  
4. **结论：** conclusion-note  

## 自检（组版后、短结前；打开 `<out>/report.html` 用搜索核对）

缺任一项 = 未完成：回到对应步骤重跑，不要只改措辞交差。

### A. 文件是否落盘

| 检查 | 通过标准 | 失败时 |
|------|----------|--------|
| PDF | 存在产出目录下 `report.pdf` 且体积明显大于空壳 | 重跑 `scripts/compose_pdf.py`（见本 Skill `SKILL.md` 步骤3.3） |
| HTML | 存在产出目录下 `report.html` | 重跑 `scripts/compose_html.py`（见本 Skill `SKILL.md` 步骤3.2） |
| 出图 | 产出目录下 `figures/` 非空 | 重跑本 Skill `SKILL.md` **步骤2**：`scripts/render_figures.py` |
| note 落盘 | 组版后应有产出目录 `report_sections/intro_note.txt`、`sensitivity_note.txt`、`curves_notes.txt`、`conclusion_note.txt`（可为空内容） | 确认调用的是 `scripts/compose_html.py`（会写入上述四个文件） |

### B. 三张表（在 `report.html` 里搜标题/表头）

| 检查 | 通过标准 | 失败时 |
|------|----------|--------|
| 介绍字段表 | 能搜到「型号/产品」；表中产品名与 `params.json` 的 `product` 一致 | 查 params；重跑 compose |
| 灵敏度明细 | 能搜到标题 **灵敏度明细**；表中有多行样机名，且能对上 sheet `sensitivity` 的样机 | 查 `sensitivity` sheet；重跑 compose；**禁止**手写补表 |
| 灵敏度分档计数 | 能搜到标题 **灵敏度分档计数**；有「幅度范围」列和「样机数」列 | 同上 |

### C. 曲线图（看 `figures/` 文件名 + HTML 是否引用）

至少应出现（有则 HTML 的 `src` 里也能搜到文件名）：

1. `奇异值与剔异前均值.png`  
2. `归零叠图.png`  
3. 至少一张 `包络分档_正负*.png`（张数随批次 δ，短结须报张数）  
4. `金标绝对与偏差.png`  
5. 若有辅标：`辅标偏差叠图.png`、`辅标绝对叠图.png`  
6. `批量一致性sigma.png`；且图下有一致性说明文字（来自 `批量一致性说明.txt`，不是画进 PNG）

顺序须为：奇异值 → 归零 → 包络分档（按 δ 从小到大）→ 金标 → 辅标（若有）→ 一致性。

### D. 白话参数（若传了 `--*-note`）

在 `report.html` 对应节能搜到你传入的原文关键词；若未传参，介绍节仍应有脚本默认短句，表与图不受影响。

### E. 禁止项（出现则违规，须重做组版思路）

- note / 正文里又贴了一整张「灵敏度明细」或「分档计数」手写表  
- 自己新建/手改 `report_sections` 当报告节来写（应由脚本落盘）  
- 为凑自检去改 `process.md` 或手算新数  

短结时向用户汇报：PDF 路径、包络分档张数、上表 A–C 是否全部通过。
