# 步骤2：标准化核对填空（C 指向性）

填进 `process.md` 的 `## 标准化与脚本入参`（仅日志，不抄命令行表）。

## 核对清单（写完角度宽表后逐项核对）

- [ ] 确认表（角度×文件名）已获用户确认
- [ ] `params.json` 已写：`angles`（有序）、`axial_angle`、`sample_count`
- [ ] 每个角度一张 sheet，sheet 名 = `normalize_angle_tag(angle)`
- [ ] 各角度 sheet 列数一致 = `sample_count`；同序号同列位
- [ ] 各角度 sheet 频率列（A 列）一致
- [ ] 轴向 sheet 存在且其角度标签 = `axial_angle`
- [ ] xlsx 已生成；聊天只报：sheet 数、各 sheet 行列数、样机数

## 不自然处（必须修了再进步骤3）

- 任一角度 sheet 列数 ≠ 轴向 sheet 列数
- 同序号在不同角度 sheet 对应不同样机名
- 频率网格未对齐
- 缺轴向 sheet

## 硬规则

- 顺序：确认表 → params → xlsx → md 核对；禁止跳步。
- 本步不跑差值/一致性脚本。
