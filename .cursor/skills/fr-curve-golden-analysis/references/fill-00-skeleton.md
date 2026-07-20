# 步骤0：process.md 骨架（A 选标）

公共版式真源：[`../../shared/references/fill-00-skeleton.md`](../../shared/references/fill-00-skeleton.md)

A 选标按公共骨架填入 `process.md`，并追加下列 **A 专有章**（步骤3 由脚本写入）：

```markdown
## 灵敏度分析          ← 步骤3 由脚本写入
## 奇异值分析          ← 步骤3 由脚本写入；确认后脚本再补「用户决定」
## 曲线分析            ← 步骤3 确认剔异后由脚本写入
```

## A 默认频段

`f_lo_hz=100`, `f_hi_hz=15000`（**必须用户确认**；可改）。

## params 模板

A 的 [`params.template.json`](params.template.json) 基于 shared base + A 专有字段（`sensitivity.*` / `curves.*`）。
