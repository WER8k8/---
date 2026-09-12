# Node 服务下线清单（T-NODE-3）

## 前置（必须全部 ✅）

- [x] FastAPI `seo_matrix` 覆盖矩阵读写
- [x] 发布/母版/计费均在 FastAPI
- [ ] 生产流量 7 日无 Node 写请求（运维日志）
- [ ] `seo-admin` 已切主 API 基址

## 下线步骤

1. 将 `seo-backend` 容器缩容为 0（保留镜像 1 个版本回滚）
2. 从 `docker-compose` / 网关删除 `3000` 矩阵 Node 上游
3. 保留 MySQL 快照只读 30 天（合规归档）
4. 更新 `docs/integrations/status` 或运维看板：Node=deprecated

## 回滚

恢复 Node 只读容器 + 网关路由；**禁止**双写。
