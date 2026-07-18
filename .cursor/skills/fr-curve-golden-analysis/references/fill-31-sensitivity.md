# 步骤3.1：灵敏度分析（版式对照）

由 `run_sensitivity.py` 写入 `process.md` 的 `## 灵敏度分析`。Agent **不要手填**；若脚本未写或格式不对，对照本文件检查。  
数字来自 `sensitivity` / `sensitivity_meta`。

```markdown
## 灵敏度分析

- 中线方式：{midline_mode}
- 中线数值：{midline_db} {unit}
- 灵敏度金标：{golden}（相对中线 {golden_delta_to_mid} dB，档位 {golden_bin}）
- 样机数：{n_samples}

| 样机 | 1000Hz ({unit}) | 相对中线 (dB) | 档位 | 角色 |
|------|----------------|---------------|------|------|
| {sample} | {level_1000} | {delta_to_mid} | {bin} | {role} |
```
