# Skill 包 19 条问题清单与修改风险评估

**日期:** 2026-07-20
**基线:** main @ `4afef13`（已含 intake-directivity-gate）
**用途:** 区分事实、规范和建议；逐条记录问题、修法、回归风险与验证方法。

## 判定口径

本文对照：

1. [Agent Skills Specification](https://agentskills.io/specification)：格式强制项。
2. [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices)：官方建议，不等于强制。
3. [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)：Agent 级评估方法。
4. Superpowers `writing-skills`：更严格的 eval-first / RED-GREEN-REFACTOR 方法。
5. 本仓目标：三个 Skill 可维护、可验证，并尽量可单独分发。

文中用词：

- **规范缺口:** 不满足 specification。
- **已验证缺陷:** 已用命令或链接校验复现。
- **工程缺口:** 不违规，但可靠性、维护性或可移植性不足。
- **可选优化:** 有收益，但不是完成标准 Skill 的必要条件。

风险只表示“修改后破坏现有功能的概率与影响”，不表示问题优先级：

| 等级 | 含义 |
|------|------|
| 极低 | 不改运行时或 Agent 主流程；静态检查即可验证 |
| 低 | 局部加性改动或命令/SOP 措辞调整；定向测试可验证 |
| 中 | 改资源路径、跨 Skill 边界或关键 SOP 信息架构；需要端到端回归 |
| 高 | 改核心算法、数据合同或用户确认语义；需要真实批次对照 |

本清单没有建议直接实施的高风险项。

---

## 一、已验证缺陷（建议第一批修）

### 1. B 报告 Skill 的测试从仓库根跑必挂

- [ ] **问题:** 按根 README 的命令 `pytest .cursor/skills/fr-curve-measurement-report/scripts/tests -q -m "not integration"` 从仓库根执行，9 个收集错误（`ModuleNotFoundError: No module named 'sensitivity_tables'`）。只有 `cd` 进 `scripts/` 才能过（32 passed）。
- **原因:** B 的 `tests/conftest.py` 缺 `sys.path.insert(0, SCRIPTS_DIR)`；C 的 conftest 有这行所以没事。
- **修法:** 照抄 C 的 conftest 头三行到 B 的 conftest。
- **风险: 极低。** 只影响测试收集，不碰运行时脚本。
- **验证:** 从仓库根和 B 的 `scripts/` 目录各跑一次测试。

### 2. 根 `requirements.txt` 缺 numpy / scipy

- [ ] **问题:** C 的 `run_cluster.py` / `run_peaks.py` 硬依赖 numpy、scipy；根 requirements 没有。按根 README 装环境跑 C 直接 ImportError。README 里"各 Skill requirements 与根目录合并内容一致"这句也已失真。
- **修法:** 根 requirements 加 `numpy>=1.24`、`scipy>=1.11` 两行。
- **风险: 低。** 不改业务逻辑，但会扩大根环境安装量并参与依赖解析。
- **验证:** 新虚拟环境按根 requirements 安装；导入 numpy/scipy；跑 C 全套测试。

### 3. 包 README 断链：灵敏度合同文件名写错

- [ ] **问题:** `.cursor/skills/README.md` 链到 `fr-curve-measurement-report/references/data-contract-sensitivity.md`，实际文件名是 `data-contract-sheets-sensitivity.md`。
- **修法:** 改链接一处。
- **风险: 极低。** 纯链接修正。
- **验证:** 重跑 markdown 相对链接校验。

### 4. A 的 SKILL.md 里有假链接 `http://process.md`

- [ ] **问题:** 步骤 2.3 标题里 `[process.md](http://process.md)` 是编辑器自动生成的垃圾链接。
- **修法:** 去掉链接，保留文字 `process.md`。
- **风险: 极低。** 纯链接修正。
- **验证:** 搜索 `http://process.md` 应为 0 个结果。

### 5. 根 README 的 Skill 列表没有 C

- [ ] **问题:** 根 `README.md` 的 Skill 表只列 A、B；测试命令没有 C；根 requirements 注释仍写“both FR skills”。
- **修法:** 增加 C 的介绍与测试命令；把数量相关措辞改为“三个 Skill”或不写数量。
- **风险: 极低。** 纯文档。
- **验证:** README 的 Skill 表、依赖说明、测试命令三处互相一致。

### 6. `--*-file` 传参：文档指空、两 Skill 实现不一致

- [ ] **问题:** 根 README 说"Windows 用 Skill 规定的 `--*-file` 方式"。实际：B 的 `compose_html.py` 实现了 `--intro-note-file` 等参数但 B 的 SKILL.md 从未提及；C 的 `compose_html.py` 压根没实现 file 参数。
- **修法（推荐拆两步）:**
  1. 文档步：准确列出 B 已实现的 `--*-note-file`；根 README 明确该能力目前仅适用于 B。
  2. 代码步（可选）：给 C 的 `compose_html.py` 补 file 参数，向 B 看齐。
- **风险: 文档步极低；代码步低。** C 加参数应保持现有 `--*-note` 行为不变。
- **验证:** B 文档示例实跑；若补 C 参数，新增 file 与 inline 内容等价测试。

---

## 二、质量保障缺口（建议第二批修）

### 7. A 的核心脚本零测试

- [ ] **问题:** A 只有 `test_outliers.py`（3 个用例）。714 行的 `run_curves.py`（金辅标排名核心）、345 行的 `run_sensitivity.py`、`params_io.py` 全部没有测试。C 有 64 个用例、B 有 32 个作对照。A 恰是数字正确性要求最高的一环。
- **修法:** 照 C 的 conftest 模式给 A 建合成夹具，覆盖：灵敏度分档、中线两种模式、奇异值两阶段（pending→confirmed）、排名与辅标数、exclude 各种取值。
- **风险: 极低。** 纯新增测试；可能暴露已有 bug，但不会制造功能回归。
- **验证:** 新用例先能对当前行为给出明确结果；再纳入全套 pytest。

### 8. 同名脚本的“共用还是分叉”没有定义

- [ ] **问题:** md5 不同不等于逻辑不同。复核后：`compose_pdf.py`、`quantize.py`、A/C 的 `params_io.py` 主要是注释差异；`plot_style.py` 则是有意分叉，B 多了报告专用绘图函数。当前没有文件说明哪些必须等价、哪些允许不同。
- **修法:** 保留每个 Skill 内的自包含副本；记录“等价组”和“有意分叉组”。对等价组加轻量 parity 测试，或至少在 CI 中比较公共函数行为。
- **风险: 低。** 文档与测试本身不改运行时；不要抽成 `shared/scripts/`，否则破坏单 Skill 分发。
- **验证:** parity 测试通过；有意分叉列表与实际 diff 对得上。

### 9. 没有 CI

- [ ] **问题:** 三套 pytest 全靠手跑，问题 1 挂了很久没人发现就是后果。
- **修法:** 加一个最小 GitHub Actions：装根 requirements，分别跑 A、B（`-m "not integration"`）、C 三套测试。
- **风险: 极低。** 不改产品运行时，但可能让已有缺陷阻断后续合并。
- **验证:** **先修 1、2**，再确认 CI 三个 job 全绿。

---

## 三、规范语义与可移植性（建议第三批修）

### 10. 静态模板没有按 `assets/` 语义归类

- [ ] **性质:** **官方建议，不是规范违规。** Specification 明确 `assets/` 可选，也允许其它目录；但它把“templates, resources”归到 `assets/`。当前放法不会导致 validate 失败。
- **问题:** B/C 的 `report.html.j2`、`report.css` 是输出模板却放在 `scripts/templates/`；A/C 的 `params.template.json` 也是待复制模板，却放在 `references/`。目录语义不清。
- **修法:** 报告模板迁到各 Skill 的 `assets/templates/`；params 模板迁到各自 `assets/`。与第 12 条一起处理，避免迁完仍依赖 Skill 根外的 shared 模板。
- **风险: 中。** 这是全清单里唯一真正动运行时代码路径的一条。漏改任何一处则组版直接挂。兜底：B、C 都有 compose 冒烟测试，迁完全量跑一遍即可放心；建议单独一个 PR，别和其他条混。
- **验证:** B/C 组版测试、HTML 冒烟、params 模板复制路径测试全部通过。

### 11. 运行环境要求没有进入 `compatibility`

- [ ] **性质:** `compatibility` 是可选字段；官方只建议在确有环境要求时填写。本包确实有 Python、第三方包和 Playwright Chromium 要求。
- **问题:** 三个 SKILL.md 的 frontmatter 没写这些要求，用户只有读根 README 才知道。
- **修法:** A 写 Python/openpyxl；B/C 写 Python 依赖与生成 PDF 需要 Chromium。`metadata`、`license` 不为“凑齐字段”硬加，见第 17 条。
- **风险: 低。** YAML 写坏会导致 Skill 加载失败。
- **验证:** `skills-ref validate` + Cursor 中确认三个 Skill 仍可发现。

### 12. A / C 依赖 Skill 根目录外的 `shared/`

- [ ] **问题:** A/C 的 SKILL.md 和本地 reference 使用 `../shared/`、`../../shared/`。整包在 Cursor 仓库里能用，但单独复制、上传或发布一个 Skill 时会断。Specification 的可移植单元是一个 Skill 目录，文件引用应从 Skill 根出发。
- **修法:** 分发产物必须自包含。推荐把公共 reference/materialize 到 A、C 各自目录，并用包级同步脚本或 parity 测试保证副本一致；不要让运行中的 Skill 跨根读取 shared。
- **风险: 中。** 会改多处链接、模板来源和安装姿态。
- **验证:** 分别只拷 A、只拷 C 到临时 skills 目录；链接校验和步骤 0–1 冒烟均通过。

### 13. 没有 Agent 级 eval，只测了 Python

- [ ] **纠偏:** C 当前 description 写的是“做什么 + 何时用”，这符合官方 specification；它没有展开步骤顺序，不应判为问题。全英文也不是规范问题，是否补中文必须靠触发数据判断。
- **真正缺口:** 三个 Skill 都没有 `evals/evals.json`，没有 with-skill / without-skill（或旧版）对照，也没有 should-trigger / should-not-trigger 查询集。Python 单测只能证明脚本，不证明 Agent 会触发、读对 reference、守住闸门。
- **修法:** 每个 Skill 先建 2–3 个真实任务 eval；另建中英文触发集（含 A/B/C 近邻反例）。任何 description 或瘦身改动都先跑旧版基线，再改，再对照。
- **风险: 极低。** 纯新增评估；成本是运行时间与模型调用量。
- **验证:** 保存基线、断言、实际输出和对照结果；不能只写“手工检查通过”。

### 14. 命令示例用 `^` 续行符（仅 Windows cmd 有效）

- [ ] **问题:** B、C 的多行命令示例用 `^` 续行。macOS / Linux bash 照抄会把 `^` 当字面量，命令报错。README 却说三平台支持。
- **修法:** 命令示例改单行（Agent 复制执行不在乎长短），或分平台各给一版。
- **风险: 低。** 纯文档，但命令是 Agent 的实际执行入口。
- **验证:** Windows 与 bash 各实跑至少一条完整组版命令。

### 15. A / C 与 B 的脚本路径写法不统一

- [ ] **问题:** A、C 的命令写死 `.cursor/skills/...`（假设 cwd = 仓库根）；B 用"本 Skill 根目录"（可单独拷走）。两种哲学并存。
- **修法:** A、C 向 B 看齐，统一为"本 Skill 根目录"写法。
- **风险: 低。** 纯文档，但改的是 Agent 实际要执行的命令模板，改完要人眼核对每条命令路径正确。
- **验证:** 在非仓库根 cwd 中分别执行 A/C 一条命令。

### 16. 重复文本人肉同步，早晚漂移（瘦身主战场）

- [ ] **问题:** intake 表、探查套路和串行铁律都有重复；其中一部分浪费 SKILL.md 上下文，一部分是为自包含或可靠性而必须保留的副本，不能一律按 DRY 删除。
- **修法:** 按第五节区分三种内容：细节移到 Skill 根内的直接 reference；关键禁令保留简短内联；跨 Skill 公共源只用于生成/校验分发副本。
- **风险: 中。** 改的是 Agent 实际读取的信息架构。
- **验证:** 必须先有第 13 条旧版基线，再逐项做行为对照；不接受只看行数和链接的静态验收。

### 17. 对外发布信息尚未定义

- [ ] **性质:** 这些都不是 Skill 格式强制项；只在对外分发、版本发布或示例确有教学价值时需要。
- **问题:** 仓库已经以“包”姿态写安装说明，却没有明确授权方式和版本标识；旧缺口文档也无法代替 changelog。
- **修法:** 先由所有者决定许可证；准备发布时再加包版本与 CHANGELOG。examples 只在 eval 证明 Agent 看示例会更好时添加，不为目录齐全而添加。
- **风险: 极低。** 纯元数据/文档；许可证内容必须由所有者确认，Agent 不代做法律决定。
- **验证:** README、LICENSE、frontmatter 引用一致；版本发布时有对应 changelog 条目。

### 18. 没跑过官方 `skills-ref validate`

- [ ] **问题:** frontmatter / 命名合规靠人眼，没进流程。
- **修法:** 本地或 CI 里对三个 Skill 目录各跑一次 validate；写进维护约定。
- **风险: 极低。** 只读校验。
- **验证:** 三个 `skills-ref validate` 均返回成功；建议接入 CI。

---

## 四、文档卫生

### 19. 旧缺口清单已经过时，但没有标为“已替代”

- [ ] **问题:** `docs/superpowers/specs/2026-07-17-mic-fr-skills-package-gap-analysis.md` 仍写 C 未创建、README 过时等旧事实；末尾虽然有修订备注，但主体大量结论已失效，容易误导维护者。
- **修法:** 文件顶部加醒目的“已由本文替代”说明和链接；保留旧文作为历史，不继续逐段修补。
- **风险: 极低。** 纯文档状态标记。
- **验证:** 从旧文首屏即可跳到本文。

**纠偏说明:** `.superpowers/sdd/task-5-report.md` 不是“漏提交”。git 历史显示它被有意创建并再次提交补全 commit SHA；是否长期保留属于仓库归档策略，不能在没有证据时列为缺陷。

---

## 五、瘦身专项（第 16 条拆解）

### 先定原则

1. **优化加载进上下文的内容，不追求磁盘行数最少。** 本地 reference 副本不被读取时没有 token 成本。
2. **自包含优先于跨 Skill DRY。** 为少几行而依赖 `../shared/`，会牺牲单 Skill 分发。
3. **关键 gotcha 留在 SKILL.md。** 串行门禁这类不容易自行推断的规则，不能只藏在外链。
4. **SKILL.md 直接链接需要的 reference。** 不让 Agent 经 reference 再追第二层 reference。
5. **先有第 13 条 eval 基线，再删文字。** 不能凭“看着重复”判断 Agent 不需要。

按当前行数估算，合理瘦身约 **50–70 行**：A 的 SKILL.md 可缩约 20%–28%，三个 SKILL.md 合计约缩 6%–9%。原先“全包约 15%”的估计偏高，已纠正。

### 瘦1. A 的 intake 表移出主文件

- [ ] **现状:** intake 信息在 A 的 SKILL.md、shared skeleton、intake-confirm 三处重复。
- **修法:** A 的 SKILL.md 只保留步骤目标、A 专有默认和硬闸门，并**直接**链接 A 根内的 `references/intake-confirm.md`。该本地文件可由包级源生成，但运行时不得跨 Skill 根。
- **收益:** 约 20–25 行；主流程更易扫读。
- **风险: 中。** Agent 若没打开 reference，会漏确认项。
- **前置/验证:** 先完成 12、13；用旧版对照新版跑 A 步骤 0 eval，确认所有必问项、C 意向和默认值都出现。

### 瘦2. A 的探查套路移到本地 reference

- [ ] **现状:** 探查六步、置信度聊天表和问法示例，在 A 主文件与 shared reference 重复。
- **修法:** A 的 SKILL.md 留“何时读、完成标准、不过闸不继续”；细节放 A 根内的 `references/fill-01-explore.md`，由 SKILL.md 直接链接。
- **收益:** 约 30–40 行。
- **风险: 中。** 这是行为说明，不只是背景资料；引用不明确会导致 Agent 先探查后读规则。
- **前置/验证:** 先跑旧版步骤 1 eval；新版必须先读 reference，再探查，并保持映射表与置信度行为不变。

### 瘦3. 串行铁律减少赘述，但保留内联不变量

- [ ] **现状:** A、C、包 README、shared README 多处展开，且“可提前收意向”与“何时算开始 C”已有措辞差异。
- **修法:** 包 README 留完整解释；A/C 的 SKILL.md 各保留相同的 2–3 行不变量：可提前确认 C 意向，但 A（及所需 B）完成前不得建 C 产出、写 C 宽表或跑 C 脚本。删掉同一文件内的重复段落，不把核心禁令只留成外链。
- **收益:** 约 10–15 行；重点是消除矛盾，不是追求大幅减字。
- **风险: 低。** 核心禁令仍内联。
- **验证:** A+C、A+B+C、仅 C 三个流程 eval 都通过。

### 瘦4. C 的命令块合并（评估后不建议做）

- [ ] **现状:** C 有多段相似命令，表面上可再省约 30 行。
- **判断:** **不做。** 每条命令的脚本名、顺序、产出和失败条件不同；显式写出可降低 Agent 拼错命令的概率。这里的重复换来了低自由度，符合官方“脆弱任务要更具体”的建议。
- **风险:** 若强行合并为模板，回归风险为中；Agent 要自行拼命令，收益可能为负。

### 明确不瘦

- B 的 SKILL.md：217 行，已按步骤渐进披露；再压会伤闸门。
- 数据合同 reference：按消费者拆分合理。超过 100 行的两份合同可补目录，但不应合并。
- `docs/superpowers/`：不被 Skill 自动加载，不是上下文成本。

---

## 六、建议批次

| 批次 | 条目 | 特点 |
|------|------|------|
| 1 | 1、2、3、4、5、6（文档步）、19 | 已验证缺陷；极低到低风险 |
| 2 | 7、9、13、18 | 先建立脚本测试、CI、Agent eval、格式校验 |
| 3 | 8、11、14、15、17 | 不改目录边界的正规化；低风险 |
| 4 | 10 + 12 | assets 归位与 Skill 自包含一起设计；中风险、单独 PR |
| 5 | 16 = 瘦1 + 瘦2 + 瘦3 | 必须在 12、13 后；一次只瘦一项并对照 eval |
| 可选 | 6(代码步：C 补 file 参数)、瘦4 | 瘦4 默认不做 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：基于 `4afef13` 全仓遍历 + 三套测试实跑 + 链接全量校验 |
| 2026-07-20 | 增瘦身专项：第 16 条拆为瘦1–瘦4 并逐条评估风险；批次表同步 |
| 2026-07-20 | 第一性原理复核：区分强制规范/官方建议；纠正 assets、description、SDD 报告三处判断；补自包含与 Agent eval 缺口；重做瘦身原则和批次顺序 |
