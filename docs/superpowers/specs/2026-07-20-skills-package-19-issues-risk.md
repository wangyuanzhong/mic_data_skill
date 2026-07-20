# Skill 包 19 条问题清单与修改风险评估

**日期:** 2026-07-20
**基线:** main @ `4afef13`（已含 intake-directivity-gate 落地）
**对照标准:** agentskills.io 官方规范 + Superpowers `writing-skills` 准则
**用途:** 逐条列问题、修法、以及**修它对现有功能的风险**。修完一条勾一条并注明日期。

风险等级说明：

| 等级 | 含义 |
|------|------|
| 无 | 纯文档或纯新增，不碰任何现有行为 |
| 低 | 碰到 Agent 触发/SOP 措辞或加性代码，理论上可能影响行为，容易验证 |
| 中 | 改代码路径或改 Agent 实际执行的 SOP 结构，需要测试兜底 |

---

## 一、硬伤（跑起来会坏；建议第一批修）

### 1. B 报告 Skill 的测试从仓库根跑必挂

- [ ] **问题:** 按根 README 的命令 `pytest .cursor/skills/fr-curve-measurement-report/scripts/tests -q -m "not integration"` 从仓库根执行，9 个收集错误（`ModuleNotFoundError: No module named 'sensitivity_tables'`）。只有 `cd` 进 `scripts/` 才能过（32 passed）。
- **原因:** B 的 `tests/conftest.py` 缺 `sys.path.insert(0, SCRIPTS_DIR)`；C 的 conftest 有这行所以没事。
- **修法:** 照抄 C 的 conftest 头三行到 B 的 conftest。
- **风险: 无。** 只影响测试收集，不碰任何运行时脚本。修完从仓库根和 scripts 目录各跑一遍验证即可。

### 2. 根 `requirements.txt` 缺 numpy / scipy

- [ ] **问题:** C 的 `run_cluster.py` / `run_peaks.py` 硬依赖 numpy、scipy；根 requirements 没有。按根 README 装环境跑 C 直接 ImportError。README 里"各 Skill requirements 与根目录合并内容一致"这句也已失真。
- **修法:** 根 requirements 加 `numpy>=1.24`、`scipy>=1.11` 两行。
- **风险: 无。** 纯加性；C 自己的 `scripts/requirements.txt` 本来就有这两行，不会引入版本冲突。

### 3. 包 README 断链：灵敏度合同文件名写错

- [ ] **问题:** `.cursor/skills/README.md` 链到 `fr-curve-measurement-report/references/data-contract-sensitivity.md`，实际文件名是 `data-contract-sheets-sensitivity.md`。
- **修法:** 改链接一处。
- **风险: 无。** 纯文档。

### 4. A 的 SKILL.md 里有假链接 `http://process.md`

- [ ] **问题:** 步骤 2.3 标题里 `[process.md](http://process.md)` 是编辑器自动生成的垃圾链接。
- **修法:** 去掉链接，保留文字 `process.md`。
- **风险: 无。** 纯文档。

### 5. 根 README 的 Skill 列表没有 C

- [ ] **问题:** 根 `README.md`"包含的 Skill"表只列 A、B；C（指向性）已存在多日但没进表。测试命令一节也没有 C 的 pytest 命令。
- **修法:** 表里加 C 一行；跑测试一节加 C 的命令。
- **风险: 无。** 纯文档。

### 6. `--*-file` 传参：文档指空、两 Skill 实现不一致

- [ ] **问题:** 根 README 说"Windows 用 Skill 规定的 `--*-file` 方式"。实际：B 的 `compose_html.py` 实现了 `--intro-note-file` 等参数但 B 的 SKILL.md 从未提及；C 的 `compose_html.py` 压根没实现 file 参数。
- **修法（推荐拆两步）:**
  1. 文档步：B 的 SKILL.md 补一句"Windows 长文本用 `--*-note-file`"；根 README 措辞对齐现状。
  2. 代码步（可选）：给 C 的 `compose_html.py` 补 file 参数，向 B 看齐。
- **风险: 文档步无；代码步低。** C 加参数是纯加性（现有 `--*-note` 参数不动），但要补对应测试用例，并确认 note 文件读入后与命令行传参走同一渲染路径。

---

## 二、短板（质量洼地；建议第二批修）

### 7. A 的核心脚本零测试

- [ ] **问题:** A 只有 `test_outliers.py`（3 个用例）。714 行的 `run_curves.py`（金辅标排名核心）、345 行的 `run_sensitivity.py`、`params_io.py` 全部没有测试。C 有 64 个用例、B 有 32 个作对照。A 恰是数字正确性要求最高的一环。
- **修法:** 照 C 的 conftest 模式给 A 建合成夹具，覆盖：灵敏度分档、中线两种模式、奇异值两阶段（pending→confirmed）、排名与辅标数、exclude 各种取值。
- **风险: 无（对功能）。** 纯新增测试，不改产品代码。注意：新测试可能暴露 A 脚本里已有的真 bug——那是收益不是风险，但要有心理预期。

### 8. 同名脚本 B / C 各存一份且已分叉

- [ ] **问题:** `params_io.py`、`plot_style.py`、`quantize.py`、`compose_pdf.py` 在 B、C 各一份，md5 已不同。一边修 bug 另一边不会跟，没有同步机制。
- **修法（推荐保守方案）:** 不合并代码（合并会破坏"Skill 可单独拷走"原则）。在包 README 维护约定里加一条："改这四个文件必须 diff 对侧同名文件，确认是否同步"，并列出当前有意分叉点。
- **风险: 无（保守方案）。** 纯文档约定。若选择激进方案（抽 `shared/scripts/` 公共库），风险为**中**：两边 import 路径全改、单独分发就断，不推荐。

### 9. 没有 CI

- [ ] **问题:** 三套 pytest 全靠手跑，问题 1 挂了很久没人发现就是后果。
- **修法:** 加一个最小 GitHub Actions：装根 requirements，分别跑 A、B（`-m "not integration"`）、C 三套测试。
- **风险: 无。** 纯新增；对现有功能零影响。**依赖问题 1、2 先修**，否则 CI 首跑就红。

---

## 三、正规化（不影响跑，但不标准；建议第三批修）

### 10. 报告模板放在 `scripts/templates/`，标准位置是 `assets/`

- [ ] **问题:** `report.html.j2` + `report.css`（B、C 各一份）是输出资源不是代码，按 agentskills.io 应放 `assets/`。混在 scripts 里容易被当代码误改。
- **修法:** B、C 各自 `scripts/templates/` → `assets/templates/`；同步改三处：两个 `compose_html.py` 里的 `tpl_dir`（各一行，`parent / "templates"` → `parent.parent / "assets" / "templates"`）、两份 SKILL.md 里"改排版只改 `scripts/templates/`"的字句、B/C 测试里涉及模板路径的用例。
- **风险: 中。** 这是全清单里唯一真正动运行时代码路径的一条。漏改任何一处则组版直接挂。兜底：B、C 都有 compose 冒烟测试，迁完全量跑一遍即可放心；建议单独一个 PR，别和其他条混。

### 11. frontmatter 缺可选字段

- [ ] **问题:** 三个 SKILL.md 只有必填的 `name` / `description`。缺 `compatibility`（B/C 依赖 Playwright chromium，这条最值得写）、`metadata`（包名/版本/角色）、`license`。
- **修法:** 每个 SKILL.md 的 YAML 头补三个字段。
- **风险: 低。** 加性改动，但 YAML 写坏会导致整个 Skill 加载失败。修完必须验证 Skill 还能被 Cursor 识别触发（或跑 `skills-ref validate`）。

### 12. description 全英文，用户全中文

- [ ] **问题:** 三个 description 是英文，正文和用户交互全中文。中文提问的语义触发大概率能中，但没有中文关键词兜底。
- **修法:** description 里补中文关键词（选标 / 金标 / 指向性 / 频响 / 灵敏度 / 出报告），保持 1024 字符内。
- **风险: 低。** 只影响触发召回，方向是变好；但 description 是触发的唯一依据，改完要用几句典型中文/英文提问各验一次触发。

### 13. C 的 description 复述了工作流

- [ ] **问题:** C 的 description 写了"compute … and produce …"，把做什么复述了一遍。按 Superpowers SDO 准则，description 只写触发条件；复述流程会让 Agent 走捷径不读正文。
- **修法:** 改成纯触发条件 + Do-not-use 互斥，去掉产出描述。
- **风险: 低。** 同 12：触发行为会变，改完验证触发；正文 SOP 一字不动。

### 14. 命令示例用 `^` 续行符（仅 Windows cmd 有效）

- [ ] **问题:** B、C 的多行命令示例用 `^` 续行。macOS / Linux bash 照抄会把 `^` 当字面量，命令报错。README 却说三平台支持。
- **修法:** 命令示例改单行（Agent 复制执行不在乎长短），或分平台各给一版。
- **风险: 无到低。** 纯文档；改完确认命令本身没抄错参数即可。

### 15. A / C 与 B 的脚本路径写法不统一

- [ ] **问题:** A、C 的命令写死 `.cursor/skills/...`（假设 cwd = 仓库根）；B 用"本 Skill 根目录"（可单独拷走）。两种哲学并存。
- **修法:** A、C 向 B 看齐，统一为"本 Skill 根目录"写法。
- **风险: 低。** 纯文档，但改的是 Agent 实际要执行的命令模板，改完要人眼核对每条命令路径正确。

### 16. 重复文本人肉同步，早晚漂移（瘦身主战场）

- [ ] **问题:** 同一段规则在多个文件各存一份：intake 表三份、探查套路两份、串行铁律四份（明细见下文「六、瘦身专项」瘦1–瘦3）。每次改要人肉同步，这次 intake-gate 更新同步对了，下次未必。
- **修法:** 按「六、瘦身专项」逐条执行，真源各留一处，其余压成强制引用。
- **风险:** 见「六、瘦身专项」逐条评估。整体建议单独 PR。

### 17. 没有 LICENSE / 版本号 / CHANGELOG / examples

- [ ] **问题:** 对外分发四件套全缺。README 自己也写了"对外发布前请自行补充 LICENSE"。
- **修法:** 加 LICENSE（对内可先 Proprietary）；包 README 加版本号与简短 CHANGELOG；B 加 `examples.md`（合成路径 walkthrough，不进真实数据）。
- **风险: 无。** 全部纯新增。

### 18. 没跑过官方 `skills-ref validate`

- [ ] **问题:** frontmatter / 命名合规靠人眼，没进流程。
- **修法:** 本地或 CI 里对三个 Skill 目录各跑一次 validate；写进维护约定。
- **风险: 无。** 只读校验，不改任何文件。若和 11 一起做可互相验证。

---

## 四、卫生（新发现）

### 19. SDD 中间产物 `.superpowers/sdd/task-5-report.md` 漏提交进仓

- [ ] **问题:** 这是 subagent-driven-development 流程的任务评审报告，任务 1–4 的都没进仓，只有这份漏进来。已确认仓库内无任何文件引用它。
- **修法:** `git rm` 掉；`.gitignore` 加 `.superpowers/`。
- **风险: 无。** 无引用、无功能。

---

## 六、瘦身专项（第 16 条的拆解；预计全包 SOP 文本省约 15%）

原则：真源只留一处，其余位置压成一句**强制引用**（措辞用「按 xxx 执行（强制）」，不用「参见」）。C 已经全程用引用式写法且运转正常，证明这条路走得通；A 是唯一没改造的。

### 瘦1. intake 表三份合一

- [ ] **现状:** 公共 intake 表在三处各一份：A 的 SKILL.md 步骤 0、`shared/references/fill-00-skeleton.md`、`shared/references/intake-confirm.md`（带默认值的确认包版）。
- **修法:** 真源定为 `intake-confirm.md`（最新、带默认值、带意向 gate）。`fill-00-skeleton.md` 的表删掉，只留骨架模板 + 一句强制引用；A 的 SKILL.md 步骤 0 表删掉，改一句强制引用 + A 专有行（100–15000 频段默认）。
- **收益:** 约 25 行；更重要的是改 intake 规则从改三处变改一处。
- **风险: 中。** 步骤 0 是开工闸门，A 的 Agent 必须真的打开 `intake-confirm.md` 才能拿到确认包内容。如果引用措辞不够强，Agent 可能凭 SKILL.md 残留信息就开工，漏问必确认项。兜底：引用句写成硬规则（「未按 intake-confirm.md 贴出确认包并获确认 → 禁止探查」）；改完用真实数据把 A 步骤 0 走一遍，核对确认包是否完整贴出。

### 瘦2. A 的探查套路与 fill-01 去重

- [ ] **现状:** 探查六步（文件→sheet→区域→频率→样机）、置信度聊天表、❌/✅ 问法示例，在 A 的 SKILL.md 步骤 1 与 `shared/references/fill-01-explore.md` 逐字重复。C 的 SKILL.md 步骤 1 只写一句「按 fill-01-explore.md 执行」+ C 专有维度（角度切分），干净得多。
- **修法:** A 照抄 C 的写法：步骤 1 正文压成引用 + 保留 A 的 1.3 硬规则。
- **收益:** 约 30–40 行，A 的 SKILL.md 从 251 行降到 210 左右。
- **风险: 低到中。** 比瘦1 低一档，因为 fill-01 本来就是步骤 1 的点名必读文件（A 的 1.2 已要求打开它填空），Agent 反正要开；风险只在「探查动作发生在打开 fill-01 之前」的时间窗。兜底：把「先读 fill-01 再探查」写进步骤 1 开头；同样走一遍真实数据回归。

### 瘦3. 串行铁律四处压缩

- [ ] **现状:** 「同批 A→B→C 禁止并行」在四处展开：包 README（最全）、A 铁律 5（一大段）、C 的 Overview + 铁律 7（两处）、`shared/README.md` 一条。`intake-confirm.md` 落地后又加了「开局可先收意向」的例外，四处措辞已开始各说各话（A 说「才允许写 C 宽表/跑 C 脚本/建 C 产出目录」，C 说「才开始本 Skill 步骤0」——严格读起来已经互相矛盾：意向收集本身就是步骤 0 的一部分）。
- **修法:** 真源定为包 README「同批多 Skill 串行铁律」+ `intake-confirm.md`「同批串行」节（两者先对齐合并成一处）。A、C、shared README 各压成一句：「同批禁止并行，边界以包 README 为准（强制）」。
- **收益:** 约 20 行；消除已出现的措辞矛盾。
- **风险: 低。** 铁律是禁止性规则，卫星位置压缩后禁令本身仍在（一句话也够触发「去读真源」）；且串行违规是流程级错误，用户容易当场发现。兜底：合并真源时逐句核对四处现有措辞，把最严格的版本留下。

### 瘦4. C 的六个命令块合并（可选，默认不做）

- [ ] **现状:** C 步骤 3.1–3.6 六个命令块几乎相同，只有脚本名不同（`run_deltas` / `run_freq_bins` / `run_consistency` / `run_cluster` / `run_peaks` + render）。
- **修法:** 可压成一个命令模板 + 一张「步骤→脚本名→产出 sheet」表，省约 30 行。
- **风险: 低，但收益可能为负。** 逐条显式命令是 Agent 执行稳定性的来源之一（写死了顺序和参数，没有发挥空间）；合并成模板后 Agent 要自己拼脚本名，多一次出错机会。**建议不做**，列在这里只为完整。

### 明确不瘦（看过了，没有肥肉）

- B 的 SKILL.md（217 行）：每步只读点名文件的设计本身就是省上下文的，再压会伤闸门。
- `references/` 全部小文件（15–53 行）：数据合同按消费者拆开正是标准做法。
- `docs/superpowers/` 的 spec/plan：不进 Agent 上下文，长短无所谓。

---

## 五、建议批次

| 批次 | 条目 | 特点 |
|------|------|------|
| 1 | 1、2、3、4、5、6(文档步)、19 | 全部无风险，半个 PR 的量 |
| 2 | 7、9（依赖批次 1） | 测试 + CI，纯加性 |
| 3 | 11、12、13、14、15、17、18、8(约定) | 正规化，低风险打包 |
| 4 | 10（assets 迁移） | 中风险，单独 PR，测试兜底 |
| 5 | 16 = 瘦1 + 瘦2 + 瘦3 | 先瘦3（低）再瘦2 再瘦1（中），单独 PR，真实数据回归 |
| 可选 | 6(代码步：C 补 file 参数)、瘦4 | 瘦4 默认不做 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：基于 `4afef13` 全仓遍历 + 三套测试实跑 + 链接全量校验 |
| 2026-07-20 | 增「六、瘦身专项」：第 16 条拆为瘦1–瘦4 并逐条评估风险；批次表同步 |
