# Design addendum: 奇异值 + 高Q豁免（落地现网脚本）

**日期:** 2026-07-17  
**状态:** 已确认，实现中  
**范围:** 仅曲线轨道奇异值门禁；不做 session JSON / 产出目录复用

## 流程

```
1kHz 拉平 → mean_before
  → outlier_review（含 Q≥10 豁免）
  → 用户确认剔除（门禁）
  → mean_after → 最紧δ排名（金标/辅标）
```

## 规则

- 带外（默认 &lt;100 或 &gt;15000）不参与提名
- 带内最大 |dev| 点估 Q；Q≥10 → 豁免，不建议剔除；估不出稳定 Q → 不豁免
- 建议剔除：非豁免且 max|dev| ≥ max(1.0 dB, 2×批次中位数)

## 过程落盘（必须详细）

| 文件 | 内容 |
|------|------|
| `process.xlsx` | `curve_mean_before_outlier`、`outlier_review`、`outlier_decision`、`curve_mean_after_outlier`、正式排名 sheets、`curve_meta` |
| `process.md` | 「奇异值分析」专章：规则、review 表、用户决定、剔除后样机数 |

## CLI

- 无 `--exclude`：提名 only，`outlier_gate=pending`
- `--exclude none`：确认零剔除后排名
- `--exclude A,B`：剔除后排名
