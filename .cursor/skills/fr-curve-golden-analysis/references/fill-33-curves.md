# 步骤3.3：用户决定 + 曲线分析（版式对照）

由 `run_curves.py`（`exclude` 已确认）改写「用户决定」并写入 `## 曲线分析`。Agent **不要手填**；对照本文件检查。  
数字来自 `outlier_decision` / `curve_rank` / `curve_meta`。

```markdown
### 用户决定

- 确认结果：不剔除 / 剔除 {名单}
- 进入 mean_after 的样机数：{n}
- 详见 `outlier_decision` sheet
```

```markdown
## 曲线分析

- 金标：{golden}
- 辅标：{aux}
- 分析频段：{f_lo_hz}–{f_hi_hz} Hz
- 均值：剔异后（mean_after）；剔除名单：{excluded 或 无}

| 样机 | 最紧δ | RMS | 排名 | 角色 |
|------|-------|-----|------|------|
| {sample} | {delta} | {rms} | {rank} | {role} |
```
