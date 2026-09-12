# ADR：询盘 API 主入口裁定

**状态**：已采纳（2026-05-28）  
**决策者**：产品 + 后端

## 背景

历史上存在三条询盘相关路径，导致管理端、SEO 线索与 B2B CRUD 混用。

## 裁定

| 路径 | 用途 | 状态 |
|------|------|------|
| `GET /api/v1/inquiries/unified` | **管理端列表、筛选、导出数据源** | **canonical** |
| `GET /api/v1/inquiries/` | 与 unified 同服务，兼容旧前端 | `Deprecation: true` |
| `GET /api/v1/inquiries-v2/` | 外贸 B2B 按 buyer/merchant 的 CRUD | 保留，**非**管理端列表 |
| `GET /api/v1/inquiries/portal` | 入口说明与统计 | 文档化 |

## 规则

1. 新功能、新页面只调用 **unified**（及 `export` 等同前缀子路径）。
2. 禁止新增第四条「列表」路由。
3. 旧路径返回体含 `deprecated` / HTTP `Deprecation` 头，指向 unified。

## 验收

- `GET /api/v1/inquiries/portal` → `canonical_list` 为 unified
- 管理端副驾导出：`/api/v1/inquiries/export`（不变）
