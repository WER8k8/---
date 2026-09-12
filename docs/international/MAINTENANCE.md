# 国际订单采集系统 — 运维维护指南

> 文档版本：v1.0 | 最后更新：2026-05-21
> 适用架构：Cloudflare Workers（海外）+ 阿里云轻量服务器（国内）

---

## 目录

1. [日常巡检清单](#1-日常巡检清单)
2. [监控告警配置](#2-监控告警配置)
3. [日志查看方法](#3-日志查看方法)
4. [常见问题排查](#4-常见问题排查)
5. [数据备份与恢复](#5-数据备份与恢复方案)
6. [Workers 调用配额监控](#6-workers-调用配额监控)
7. [反爬虫策略升级指南](#7-反爬虫策略升级指南)

## 1. 日常巡检清单

### 1.1 每日巡检（建议早上 9:00 执行）

| 序号 | 检查项 | 命令/操作 | 预期正常状态 |
|------|--------|-----------|-------------|
| 1 | Webhook 服务存活 | systemctl is-active international-webhook | active |
| 2 | Nginx 状态 | systemctl is-active nginx | active |
| 3 | 数据库连接 | pg_isready -h localhost -U youding_international | accepting connections |
| 4 | API 健康检查 | curl -s https://api.youdingbrick.com/health | status: healthy |
| 5 | Workers 昨日调用次数 | wrangler tail --format=json 2>&1 | wc -l | 非零 |
| 6 | 昨日新增询盘数 | psql -c "SELECT COUNT(*) FROM inquiries WHERE created_at >= now() - interval '24 hours';" | 大于 0 |
| 7 | 磁盘使用率 | df -h / | tail -1 | 使用率 < 80% |
| 8 | 内存使用率 | free -h | grep Mem | 可用内存 > 500MB |

### 1.2 每周巡检

| 序号 | 检查项 | 命令/操作 | 预期正常状态 |
|------|--------|-----------|-------------|
| 1 | SSL 证书剩余天数 | openssl x509 -enddate -noout -in /etc/letsencrypt/live/api.youdingbrick.com/fullchain.pem | 剩余 > 30 天 |
| 2 | Workers 错误率 | Cloudflare Dashboard -> Workers & Pages -> Analytics | 错误率 < 1% |
| 3 | Workers 配额使用 | Cloudflare Dashboard -> Workers & Pages -> 用量 | 不超过免费额度 80% |
| 4 | 数据库增长趋势 | psql -c "SELECT pg_size_pretty(pg_database_size('international_inquiry'));" | 记录每周增量 |
| 5 | 日志错误扫描 | grep -i 'error|exception|traceback' /var/log/international-webhook/error.log | tail -20 | 无明显新增错误 |
| 6 | 安全更新检查 | apt list --upgradable 2>/dev/null | grep -i security | 无待处理安全更新 |
| 7 | 爬虫成功率 | Cloudflare Dashboard -> crawler-worker -> Success Rate | 成功率 > 90% |

### 1.3 每月巡检

| 序号 | 检查项 | 操作 |
|------|--------|------|
| 1 | 备份恢复演练 | 从备份恢复至测试环境，验证完整性 |
| 2 | 数据库 VACUUM | 执行 VACUUM ANALYZE; 防止事务 ID 回卷 |
| 3 | 配额趋势分析 | 导出近 3 个月 Workers 配额使用趋势 |
| 4 | 安全审计 | 检查系统登录记录、sudo 日志、fail2ban 状态 |
| 5 | 反爬虫策略评估 | 审视被屏蔽率、是否需要更换 User-Agent 池 |
| 6 | 数据清理 | 按合规策略删除超过保留期限的旧数据 |
| 7 | 依赖版本检查 | 检查 Python/Node 依赖的 CVE 公告 |

