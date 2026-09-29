---
title: Delivery & Evidence
type: Subsystem
id: subsystem_delivery_evidence
status: active
tags: [subsystem, uj]
---

# Delivery & Evidence

- **路径**：`backend/app/services/{browser_runtime,n8n}`
- **功能与作用**：取证（Disk JSONL+DB）+ n8n 出站分发
- **状态**：`active`
- **调度/调用关系**：Hermes egress executor
- **依赖项（它用谁）**：n8n@5678（2 webhook 激活）
- **父子层级**：属于 [[project_youding|优丁 UJ B2B 外贸 SaaS]] 的子系统（SYSTEM-LOCK-02 法定不可裁减）
- **完成度信号**：见 `docs/资产盘点审计-全维度-2026-09-11.md` §2.1
