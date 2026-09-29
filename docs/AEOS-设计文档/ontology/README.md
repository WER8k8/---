---
title: ontology 映射说明
type: Meta
tags: [ontology, readme]
---

# docs/ontology/ · 结构化本体映射说明

本目录是 **obsidian-ontology-sync** 在本项目的落点：把审计结论同时存为
「人读笔记（Obsidian PRIMARY）」+「机读图（Ontology DERIVED）」。

## 自动同步
`docs/` 经 NTFS Junction 映射到 Obsidian Vault 的 `01-权威文档与系统全景/`，
因此本目录会出现在 Vault 的 `01-权威文档与系统全景/ontology/`，**无需手动复制**。

## 文件
| 文件 | 作用 |
|---|---|
| `优丁资产审计本体-2026-09-11.md` | 本体 MOC（Project 实体，frontmatter + wikilink） |
| `subsystem_*.md` | 8 大子系统节点（Subsystem 实体） |
| `risk_*.md` | 5 个风险节点（Risk 实体） |
| `task_*.md` | 4 个下一步任务节点（Task 实体） |
| `audit-graph-2026-09-11.jsonl` | 机器可读本体图（upsert/relate，兼容 skill sync.py） |
| `README.md` | 本说明 |

## 与 obsidian-ontology-sync 技能对接
技能 `sync.py` 默认扫描 `references/contacts|clients|team` 等固定路径；
本项目资产结构不同，故采用「**先写结构化笔记 + 派生 jsonl**」的方式：
- 笔记（frontmatter `type/id` + `[[wikilink]]`）即 PRIMARY 源；
- `audit-graph-2026-09-11.jsonl` 即 DERIVED 图，格式与 `sync.py write_ontology()` 一致
  （`{"op":"upsert","entity":{...}}` / `{"op":"relate","from":..,"rel":..,"to":..}`），
  可被其 `analyze` / `feedback` 直接消费。

## 重生成
```bash
python tools/gen_audit_ontology.py
```
所有数字来自 `tools/asset_audit_report.json`，改审计数据后重跑即刷新。
