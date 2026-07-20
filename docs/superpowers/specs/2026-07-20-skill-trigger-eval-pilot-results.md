# Skill 触发 Eval：真实试跑记录（2026-07-20）

**范围:** 对应 `docs/superpowers/specs/2026-07-20-skills-package-19-issues-risk.md` 第 13 条、`docs/superpowers/plans/2026-07-20-low-and-very-low-risk-fixes.md` Task 13。
**产物:** 三个 Skill 各自的 `evals/evals.json`（每份 11 条：7 应触发 + 4 应排他/不触发）+ 本文记录的 9 条真实试跑（每 Skill 2 应触发 + 1 跨 Skill 近似反例）。

---

## 方法论（及其诚实局限）

官方 [evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills) 方法假设主机（如 Claude Code）会把「Agent 是否调用了 Skill 工具」暴露成一个可观测的工具调用事件，脚本直接检测该事件。**Cursor 目前没有暴露等价的、可从外部观测的「Skill 触发」事件**给调用方检测；Skill 的自动匹配发生在 Cursor 产品内部。

因此本次试跑用的是**代理测量**，不是对 Cursor 真实触发机制的直接观测：

1. 给一个全新、无先前上下文的 `generalPurpose` 子代理，**只**提供三个 Skill 的 `name` + `description`（这正是 specification 里"启动时预加载的元数据"阶段的内容，不多给任何 Skill 正文）。
2. 附上用户的一句话提问。
3. 要求它只根据这两样东西，判断会不会在做任何其他事之前先去读某个 Skill 的完整 SKILL.md，并引用原文说明理由。
4. 不给它仓库访问权限、不许它探查仓库，避免它靠读源码"作弊"绕开纯粹基于 description 的判断。

**这测的是「三段 description 本身的语义区分力」，不是「Cursor 产品在真实会话里到底会不会加载这个 Skill」**——如果 Cursor 的真实匹配算法与本次子代理的语言理解有系统性差异，本结果不会捕捉到。这一局限没有更好的绕过方法，除非能拿到 Cursor 官方的触发观测接口。

**规模局限：** 官方方法建议每 Skill 20 条查询、每条跑 3 次、算触发率。本次因成本原因只做了一次代表性试跑：每个 Skill 选 2 条应触发（1 条显式关键词 + 1 条隐式/大白话）+ 1 条跨 Skill 近似反例，共 9 次子代理调用，每条只跑 1 次（未算触发率，只看单次判断对不对）。完整的 11×3=33 条查询集已经写进各 Skill 的 `evals/evals.json`，供以后有需要时补跑其余条目或按官方方法跑满 3 次取触发率。

---

## 试跑结果（9/9 命中）

| # | Skill / 用例 id | 提问 | 应有判断 | 子代理实际判断 | 结果 |
|---|------------------|------|----------|----------------|------|
| 1 | A / `a-explicit-1` | 帮我分析一下这批麦克风频响测量数据，选出金标和辅标 | golden-analysis | `fr-curve-golden-analysis` | ✅ |
| 2 | A / `a-casual-outlier` | 这堆csv看起来有一条曲线特别歪，帮我判断一下是不是该拿掉 | golden-analysis | `fr-curve-golden-analysis` | ✅ |
| 3 | A / `a-nearmiss-report` | 帮我把这批已经选好金标的产出目录做成正式PDF报告 | **不是** golden-analysis（应是 B） | `fr-curve-measurement-report` | ✅ |
| 4 | B / `b-explicit-1` | 选标已经做完了，产出目录在…，帮我出一份正式的PDF报告 | measurement-report | `fr-curve-measurement-report` | ✅ |
| 5 | B / `b-envelope-feature` | 报告里的图表能不能加个包络分档 | measurement-report | `fr-curve-measurement-report` | ✅ |
| 6 | B / `b-nearmiss-golden` | 帮我从头分析这批麦克风测试数据，选出金标 | **不是** measurement-report（应是 A） | `fr-curve-golden-analysis` | ✅ |
| 7 | C / `c-explicit-angles` | 这批数据有0度、90度、180度三个角度的频响文件，帮我算指向性 | directivity-analysis | `fr-curve-directivity-analysis` | ✅ |
| 8 | C / `c-peak-valley` | 帮我看看90度那批离轴曲线里有没有明显的峰谷 | directivity-analysis | `fr-curve-directivity-analysis` | ✅ |
| 9 | C / `c-nearmiss-ambiguous-angle` | 这批数据不同角度的意思是不同批次生产的样机，不是离轴角度测量… | **不触发任何 Skill**（"角度"是刻意误导关键词） | `none` | ✅ |

**子代理原始 REASONING 摘录（#9，最关键的一条，验证 description 排他措辞真的挡住了误导关键词）：**

> "The user explicitly states '不同角度的意思是不同批次生产的样机，不是离轴角度测量'... This explicitly rules out fr-curve-directivity-analysis, whose description is scoped to genuine 'multi-angle' off-axis delta/directivity analysis..."

**#3 和 #6（跨 Skill 近似反例）说明 A/B 两份 description 的互斥措辞（"Do not use for..."）在这次代理测量里确实起了作用**，没有出现"因为都是频响相关就两个都选"的模糊情况。

---

## 结论

- 9/9 通过：三份 description 目前的语义区分力（至少在本代理测量下）足以正确区分显式关键词提问、隐式/大白话提问，以及跨 Skill 近似反例，包括一条刻意设置的误导性关键词反例。
- **不构成"description 已完美/无需再测"的结论**——样本量小（9 条，每条 1 次），且方法论本身是代理测量而非 Cursor 真实触发的直接观测。
- 后续若改任一 description，应重新跑对应 `evals.json` 里受影响的条目，理想情况下按官方方法每条跑 3 次算触发率。

---

## 遗留：全量任务质量 eval 未做

官方方法的另一半——"with-skill vs without-skill 的**实际产出质量**对比"（例如让 Agent 真的走一遍选标 SOP，对比有无 Skill 时输出的 params.json/process.xlsx 质量）——本次**没有**做。原因：

1. 需要真实的频响测量原始数据（XLS/CSV/SPL），仓库里没有、也不该造假数据进仓（会话历史里明确禁止把分析产出写进仓库）。
2. 这类端到端任务质量对比比触发测试贵得多（每条要走完整 SOP，产出多个文件），受限于本次时间/成本预算未展开。

若以后要做，建议用一批**匿名化的合成测量数据**（仿照各 Skill `scripts/tests/conftest.py` 里已有的合成夹具手法）作为 eval 输入文件，而不是真实产品数据。
