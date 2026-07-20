# 步骤0：process.md 骨架（C 指向性）

公共版式真源：[`../../shared/references/fill-00-skeleton.md`](../../shared/references/fill-00-skeleton.md)

开局确认包：[`../../shared/references/intake-confirm.md`](../../shared/references/intake-confirm.md)

C 指向性按公共骨架填入 `process.md`，并追加下列 **C 专有章**：

```markdown
## 角度×文件名确认    ← 步骤1b 贴确认表后留底
## 差值分析          ← 步骤3 由脚本写入
## 一致性分析        ← 步骤3 由脚本写入
## 报告              ← 步骤4 由脚本/Agent 协作写入
```

## C 默认频段

`f_lo_hz=250`, `f_hi_hz=20000`（**必须用户确认**；可改）。

## 探查后软跳过

若可区分角度（含轴向）< 2：聊天软提示本批无离轴、指向性跳过；**不要再问**；不建/不继续 C 产出。详见 `intake-confirm.md`「探查后」。

## params 模板

C 的 [`params.template.json`](params.template.json) 基于 shared base + C 专有字段（`angles` / `axial_angle` / `sample_count` / `envelope`）。
