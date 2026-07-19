# Design: SP3 — C 走势分析（分类 + 峰谷）与报告深化

**日期:** 2026-07-19  
**状态:** 设计已定稿（brainstorming）；实现计划见后续 writing-plans  
**仓库:** `mic_data_skill`  
**范围:** 仅 C（`fr-curve-directivity-analysis`）；A/B/shared 不动

---

## 1. 目标与非目标

### 1.1 目标

在 SP1（频点差值分档）之上，给 C 加「走势分析」能力，并深化正式报告：

1. **按角度独立分类**：对该角度各样机 `delta(f)` 做无监督聚类（欧氏距离、不中心化）→ 脚本出建议类；Agent/LLM 可命名/微调（不强制用户确认）
2. **类均值峰谷**：对每类均值曲线机械找峰/谷候选（含 Q），LLM 勾选「明显」者写回 xlsx
3. **报告第 5 节「走势分析」**：分类表 + 类均值峰谷标注图 + 峰谷表（仅勾选）+ 类内叠图
4. **机械验证**：L1 pytest + L2 脚本自检（exit 3）+ L3 报告自检（exit 3）
5. **死命令**：一切数值计算以脚本对 xlsx 处理的结果为准；LLM 不算数

### 1.2 非目标

- ❌ 用户强制确认分类（已选：不强制，分错再重跑）
- ❌ DTW / Pearson 相关 / 「相关+电平」混合距离（第一版只用 raw 欧氏）
- ❌ 单体峰谷表（峰谷只在类均值上；单体以类内叠图呈现）
- ❌ 合格判定、包络、Q 豁免、奇异值
- ❌ 改 A/B/shared；改 `run_deltas` / `run_freq_bins` / `run_consistency` 业务逻辑
- ❌ Playwright 端到端（可后补）
- ❌ 解决 axial 标准化两遍（已接受）

---

## 2. 架构与数据流

### 2.1 SOP 插点（步骤 3 末、步骤 4 前）

```
3.1 run_deltas
3.2 run_freq_bins
3.3 run_consistency
3.4 run_cluster.py          ← 新：距离矩阵 + 建议类 + 复制 final（若尚无）
3.5 Agent/LLM 微调类        ← 只改 cluster_final_<tag>（不强制 askuser）
3.6 run_peaks.py            ← 新：类均值 + 候选峰谷 + Q
3.7 Agent/LLM 勾选峰谷      ← 只改 peak_candidates selected
3.8 聊天短结
4.x render + compose        ← 加走势节与图
```

### 2.2 数据流

```
delta_<tag>
  → run_cluster → cluster_dist_<tag>, cluster_suggest_<tag>, cluster_meta_<tag>
               → cluster_final_<tag>（若不存在则从 suggest 复制）
  → LLM 微调   → cluster_final_<tag>
  → run_peaks  → class_mean_<tag>, peak_candidates_<tag>（selected 初值 no）
  → LLM 勾选   → peak_candidates_<tag>.selected
  → 出图/组版  → 只读 final + selected=yes
```

### 2.3 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 / 合法边界（如 n=1 成一类） |
| 2 | 前置缺失或非法 params |
| 3 | L2/L3 自检失败 |

失败后 Agent 必须向用户说明并询问是否重跑/改 params（禁止静默跳过）。

### 2.4 铁律

1. 数值（距离、k、类均值、峰谷频率/幅度/Q）只由脚本写 xlsx  
2. LLM 只改：`cluster_final` 的类 id/类名、`peak_candidates.selected`  
3. 报告不展示轴向曲线；`envelope=null` 时不做合格判定  
4. 无 Q 豁免、无奇异值分析  

---

## 3. params schema

C `params.template.json` 新增（默认均可被用户主动覆盖；不新增 intake 必问）：

| 字段 | 默认 | 含义 |
|------|------|------|
| `cluster_k_max` | `5` | 轮廓系数搜索上限；实际上限 `min(k_max, n_clusterable)` |
| `peak_prominence_db` | `1.0` | 峰/谷最小突出度（dB） |
| `peak_min_octave` | `1/3` | 峰谷最小间隔（倍频程） |
| `peak_include_q` | `true` | 是否写 Q 列（第一版固定 true，保留开关） |

非法（`cluster_k_max≤0`、`peak_prominence_db≤0`、`peak_min_octave≤0`、非数值）→ exit 2。

分析频段仍用既有 `f_lo_hz` / `f_hi_hz`（可改）。

---

## 4. xlsx sheet 合同

每非轴向角度一套（`<tag>` = `normalize_angle_tag(angle)`）。

### 4.1 `cluster_dist_<tag>`（`run_cluster` 写）

样机×样机欧氏距离矩阵。行/列头 = 样机名（与 `delta_<tag>` 列序一致）。对角为 0；矩阵对称。

### 4.2 `cluster_suggest_<tag>`（`run_cluster` 写）

| 列 | 含义 |
|----|------|
| `sample` | 样机名 |
| `cluster_id` | 建议类 id（从 1 起）；无法参与则为 `unclustered` |
| `dist_to_center` | 到类中心（类内均值向量）的欧氏距离；unclustered 为空 |

### 4.2b `cluster_meta_<tag>`（`run_cluster` 写）

| 列 | 含义 |
|----|------|
| `k` | 候选类数 |
| `silhouette` | 该 k 的平均轮廓系数；`k=1` 时为字符串 `N/A`（不参与 argmax） |
| `chosen` | `yes`/`no`：是否为最终选中的 k |

另在 sheet 顶部或首行备注区写 `chosen_k`（与 `chosen=yes` 那一行一致）。

### 4.3 `cluster_final_<tag>`（Agent/LLM 写；脚本仅在「不存在」时从 suggest 复制）

| 列 | 含义 |
|----|------|
| `sample` | 样机名 |
| `cluster_id` | 最终类 id |
| `cluster_name` | 类名（可空；空则报告显示「类{id}」） |

**重跑 `run_cluster`：若 final 已存在则不覆盖。**

### 4.4 `class_mean_<tag>`（`run_peaks` 写）

| 位置 | 内容 |
|------|------|
| A 列 | 频率 Hz（与 delta 对齐，分析频段内） |
| 第 1 行 B 列起 | 类列名：`类{id}` 或 final 中的 `cluster_name`（同 id 取首次非空名） |
| B2 起 | 该类样机在该频点的 delta 均值（类内该频点全 None → 空） |

### 4.5 `peak_candidates_<tag>`（`run_peaks` 写）

| 列 | 含义 |
|----|------|
| `cluster_id` | 类 |
| `kind` | `peak` / `valley` |
| `freq_hz` | 中心频率 |
| `amplitude_db` | 类均值曲线在该点的幅度 |
| `q` | 品质因数；无法算则为 `N/A` |
| `prominence_db` | 突出度 |
| `selected` | `yes` / `no`（脚本初值全 `no`；LLM 只改此列） |

重跑 peaks：按 `(cluster_id, kind, freq_hz)` 匹配旧行以保留 `selected=yes`。匹配规则：在新候选中找满足 `|f_new - f_old| / f_old ≤ 0.005`（0.5%）的最近一条；多条命中取 |Δf| 最小；无命中则该旧勾选丢弃，新候选保持 `no`。

---

## 5. 脚本逻辑

### 5.1 `run_cluster.py`

**输入：** `--params`；读 `delta_<tag>`、`f_lo_hz`/`f_hi_hz`、`cluster_k_max`。

**算法：**

1. 截取分析频段内频率点。  
2. 样机对欧氏距离：仅对两端皆非 None 的频点求和；有效点数为 0 → 该机 `unclustered`，不进距离矩阵核心（或矩阵中与其相关记空并 warning）。  
3. 写 `cluster_dist_<tag>`。  
4. k ∈ `{1 … min(cluster_k_max, n_clusterable)}`：  
   - `k=1`：全体一类；silhouette = `N/A`（不参与 argmax）  
   - `k≥2`：层次聚类 **average linkage**，在预计算欧氏距离矩阵上切 k 类；算平均轮廓系数（单样本类内距离 a 约定为 0，以便 n=2 的两类可得到正轮廓）  
   - 在 k≥2 的数值 silhouette 中取最大；并列取更小 k  
   - **若所有 k≥2 的 silhouette 均 ≤ 0**（典型：曲线几乎重合仍被切成多类），则回退 `chosen_k=1`  

5. 写 `cluster_suggest_<tag>` + `cluster_meta_<tag>`。  
6. 若无 `cluster_final_<tag>`：复制 suggest（`cluster_name` 先空或 `类{id}`）；若已有 final：**不覆盖**。  
7. L2 自检失败 → 删除本步写入的 dist/suggest/meta（及本次新建的 final，若是本跑创建的）→ exit 3；通过则打印 `VERIFICATION OK: ...`。

**边界：**

- `n_clusterable=1`：k=1，exit 0  
- `n_clusterable=0`：exit 2（无可用曲线）  

### 5.2 `run_peaks.py`

**输入：** `--params`；读 `cluster_final_<tag>`、`delta_<tag>`、峰参数。

**Gate：** 缺 `cluster_final_<tag>` → exit 2。

**算法：**

1. 按 final 类聚样机，算类均值 → `class_mean_<tag>`。  
2. 对每条类均值：必须用 `scipy.signal.find_peaks`；谷对 `-mean` 再找。依赖写入 C 的 `scripts/requirements.txt`。  
   - `prominence >= peak_prominence_db`  
   - 最小间隔：相邻峰（及谷）中心频率满足 \(\lvert \log_2(f_2/f_1) \rvert \ge peak\_min\_octave\)  
3. Q：对峰用半高全宽（FWHM）相对中心频：`Q = f0 / Δf_FWHM`；谷同理在取负曲线上定义；失败 → `N/A`（不因此 exit）。  
4. 写 `peak_candidates_<tag>`，合并保留已有 selected。  
5. L2 自检：均值列与 final 类集合一致；候选频率 ∈ 分析频段；selected ∈ {yes,no}；失败 → 删坏 sheet + exit 3。

### 5.3 LLM 约束（`references/cluster-llm-rules.md`）

**分类微调：**

- 只改 `cluster_final`；禁止改 `cluster_dist` / `cluster_suggest` 数值  
- 允许：命名、合并类、把明显离群单独成类  
- 若把样机改到与距离矩阵最近邻多数类严重矛盾的类 → 必须在 `process.md` 写理由（仍不强制 askuser）  

**峰谷勾选：**

- 只改 `selected`；禁止改 freq/amplitude/q/prominence  
- 只勾「肉眼明显」的峰谷；小起伏保持 `no`  
- 报告与出图只使用 `selected=yes`  

---

## 6. 报告与出图

### 6.1 图

| 文件 | 内容 |
|------|------|
| `figures/走势_类均值_<tag>.png` | 各类均值；标注 selected 峰/谷 |
| `figures/走势_类内叠图_<tag>_类<id>.png` | 该类样机 delta 叠图（可浅画类均值） |

实现：新建 `render_trend_figures.py`（只传 `--params`），与现有 `render_figures.py` 并列；步骤 4 先跑原出图再跑走势出图。缺 final/candidates → exit 2。

### 6.2 报告章节顺序（1–6）

1. 整体介绍  
2. 差值分析  
3. 频点差值分档（可空跳过）  
4. 一致性分析  
5. **走势分析**（新；不可空跳过——SP3 默认总跑）  
6. 结论  

节 5 每非轴向角度：分类表（`cluster_final`）→ 类均值峰谷图 → 峰谷表（仅 selected）→ 类内叠图。  
可选 `--trend-note` 白话。

### 6.3 L3（`compose_html`）

写后读回：含「走势分析」；每非轴向角有分类表；selected 峰谷表列齐全（类、类型、中心频率、幅度、Q）；失败 → stderr + `SystemExit(3)`，保留 html。

---

## 7. SOP / references 改动清单

| 文件 | 改动 |
|------|------|
| `SKILL.md` | 步骤 3.4–3.7；短结顺延；铁律/交付物含 cluster/peak sheets |
| `params.template.json` | 4 个新字段 |
| `data-contract-sheets.md` | dist/suggest/final/class_mean/peak_candidates |
| `report-outline.md` | 第 5 章 + 自检项 |
| `fill-chat-summary.md` | 短结必报每角类数、勾选峰谷数 |
| `cluster-llm-rules.md` | 新建：LLM 硬约束 |
| `compose_html.py` / `report.html.j2` | 走势节 + L3 |
| `render_trend_figures.py` | 新建：走势图 |
| `requirements.txt` | 确认含 `scipy` |

`process.md`：步骤 3 由 Agent 记分类微调理由与勾选摘要（日志，非数字真源）。

---

## 8. 测试与错误处理

### 8.1 L1（pytest）

**`test_run_cluster.py`：** 两机重合→k=1；两团→k=2；缺 delta→2；自检破坏→3；final 已存在不覆盖。  

**`test_run_peaks.py`：** 合成单峰候选；无 final→2；selected 保留；非法 prominence→2。  

**`test_compose_trend.py`：** 渲染走势节；缺 sheet→2；破坏 HTML→3。  

### 8.2 错误表

| 情况 | exit |
|------|------|
| 缺 angles / 缺 delta / peaks 缺 final | 2 |
| 非法 cluster/peak params | 2 |
| n_clusterable=0 | 2 |
| L2/L3 失败 | 3 |
| n=1 正常 | 0 |
| 部分 unclustered | 0 + warning |

---

## 9. 验收标准

1. 每非轴向角产出 `cluster_dist` + `cluster_suggest` + `cluster_meta`；无 final 时自动创建 `cluster_final`  
2. 欧氏距离不中心化；k 由轮廓系数选择（k=1 的 N/A 不参与 argmax）  
3. 重跑 cluster 不覆盖已有 final  
4. `run_peaks` 写出 `class_mean` + `peak_candidates`（含 Q 列或 N/A）  
5. LLM 勾选后报告/图仅显示 selected  
6. 报告含第 5 节：分类表 + 类均值图 + 峰谷表 + 类内叠图  
7. L2/L3 失败 exit 3；前置缺失 exit 2  
8. A/B/shared 与既有 C 分析脚本业务逻辑未被改坏；全量 pytest 绿  
9. 无合格判定语；无轴向曲线图  

---

## 10. 后续

- 本 spec 用户审阅通过 → `writing-plans` 出实现计划  
- 混合距离 / 单体峰谷 / Playwright / 强制确认分类 → 另开任务  

---

## 11. 决策记录（brainstorming）

| 题 | 决定 |
|----|------|
| 分类粒度 | 按角度独立 |
| 确认闸门 | 不强制确认 |
| 峰谷对象 | 类均值 |
| 峰谷流程 | 脚本候选 → LLM 勾选 |
| 分类方法 | 脚本无监督聚类 → LLM 命名/微调 |
| 距离 | raw 欧氏，不中心化 |
| 聚类 | average linkage 层次聚类 + 轮廓系数选 k |
| 峰算法 | find_peaks；prominence≥1dB；间隔≥1/3 oct |
| Q | 表内有列 |
| 报告 | 分类表 + 类均值峰谷图 + 峰谷表 + 类内叠图 |
| 架构 | 两脚本 + 两次 LLM 回写（方案 1） |

---

## 12. 自审修订记录（2026-07-19）

初稿自审钉死 5 处歧义：

| 编号 | 问题 | 修订 |
|------|------|------|
| A | silhouette 元信息存放「二选一」 | 固定独立 sheet `cluster_meta_<tag>` |
| B | selected 保留容差两种说法 | 固定相对误差 ≤0.5% 最近匹配 |
| C | find_peaks「或等价」 | 锁定 `scipy.signal.find_peaks` + requirements |
| D | 出图扩展 vs 新脚本 | 锁定新建 `render_trend_figures.py` |
| E | `cluster_k_max` 相对 n_samples | 改为相对 `n_clusterable` |
