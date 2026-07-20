# shared（公共层；不是 Skill）

本目录**不是** Cursor Agent Skill：没有 `SKILL.md`，不参与 `description` 触发匹配。  
仅给同包其它 Skill（A 选标 / C 指向性）通过相对路径引用公共 intake、探查、确认表等约定。

## 谁引用

| 引用方 | 用到 |
|--------|------|
| `../fr-curve-golden-analysis/` | intake 公共项、探查结论版式、`intake-confirm.md` |
| `../fr-curve-directivity-analysis/` | 同上 + 角度×文件名确认表、`intake-confirm.md` |

## 维护约定

- 改 `intake-confirm.md` 须同步 A/C SKILL 步骤0。
- 改本目录下任何文件 → 同步检查两个引用方 SOP 是否仍对得上。
- **不要**在本目录加 `SKILL.md`。
- 整包安装：不要只拷单个 Skill 却不带 `shared/`；Skill 间的相对路径会断。
- 若未来要单独分发某 Skill：把所需 `shared/references/*` 拷进该 Skill 目录，或等规范侧 `includes` 一类打包能力。
- A 与 C **同批时禁止并行**（先 A 全完再 C）：真源在包根 [`../README.md`](../README.md)「同批多 Skill 串行铁律」，勿在本目录另写冲突规则。
