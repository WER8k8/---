---
title: Core Backend
type: Subsystem
id: subsystem_core_backend
status: active
tags: [subsystem, uj]
---

# Core Backend

- **路径**：`backend/app`
- **功能与作用**：多租户控制面 + API 服务（FastAPI/SQLAlchemy/PG/Celery/Redis）
- **状态**：`active`
- **调度/调用关系**：全部前端/编排层/外部子系统经 adapter 接入
- **依赖项（它用谁）**：PG229表/Redis/Celery/n8n
- **父子层级**：属于 [[project_youding|优丁 UJ B2B 外贸 SaaS]] 的子系统（SYSTEM-LOCK-02 法定不可裁减）
- **完成度信号**：见 `docs/资产盘点审计-全维度-2026-09-11.md` §2.1
