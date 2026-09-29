---
title: Hermes 内部编排
type: Subsystem
id: subsystem_hermes
status: p0_active
tags: [subsystem, uj]
---

# Hermes 内部编排

- **路径**：`backend/app/services/hermes`
- **功能与作用**：L2 DAG 编排 + 状态机 + JsonPath 数据总线 + Saga
- **状态**：`p0_active`
- **调度/调用关系**：所有执行器（site_builder/content/publish…）
- **依赖项（它用谁）**：DeepSeek Harness/Celery/ExecutorRegistry
- **父子层级**：属于 [[project_youding|优丁 UJ B2B 外贸 SaaS]] 的子系统（SYSTEM-LOCK-02 法定不可裁减）
- **完成度信号**：见 `docs/资产盘点审计-全维度-2026-09-11.md` §2.1
