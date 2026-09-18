# E-4 数据库读写分离 / 分片设计（万级租户前）

> 状态：设计文档（2026-09-18）；当前开发环境为单 PG@5433，**未启用分片**。  
> 原则：先能升级，不提前把系统拆复杂。

## 1. 现状

| 项 | 值 |
|----|----|
| 主库 | PostgreSQL 15.8 @5433 / youding_dev |
| 读库 | `DATABASE_READ_URL` 可选；未配置时读写都走主库（诚实回落） |
| 代码 | `backend/app/core/db_sessions.py` · `RoutingSession` |
| 自检 | `GET /api/v1/acquisition/ops/db-topology` |

## 2. 第一阶段：读写分离（已具备代码）

```
写路径  → mark_write(session) / flush → 主库
读路径  → get_read_session() / RoutingSession 非写 → 读库（若配置）
```

生产建议：

```env
DATABASE_URL=postgresql://user:pass@primary:5433/youding
DATABASE_READ_URL=postgresql://user:pass@replica:5433/youding
```

报表类 API（流失报表、账单解释、队列监控）已标注可走只读会话。

## 3. 第二阶段：租户级逻辑隔离（中期）

- 所有业务表带 `tenant_id`（已在获客链落地）
- RLS / 应用层强制过滤（仓库已有 RLS 策略雏形）
- 大租户可迁独立 schema/database（逻辑分片）

## 4. 第三阶段：物理分片（万级租户，仅设计）

| 维度 | 建议 |
|------|------|
| 分片键 | `tenant_id` hash |
| 单元 | 单元化网关按租户路由到 shard |
| 全局表 | users 登录、billing 汇总保留全局库 |
| 挑战 | 跨租户运营查询、账单对账、迁移工具 |

**红线**：在串联率与业务闭环稳定前，不做物理分片改造。

## 5. 验收

- [ ] 配置 `DATABASE_READ_URL` 后 `/ops/db-topology` 显示 read_configured=true
- [ ] 只读探活 API 返回当前库名
- [ ] 写路径仍落主库
- [ ] 未配置读库时不报错、不假装已分离
