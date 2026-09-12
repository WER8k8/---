# Talking-Stick 安全审计报告

**任务ID**: scan_20260722_090320_2619552641488
**生成时间**: 2026-07-22 09:03:22
**扫描目标**: C:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend\app\services

## 执行摘要

| 指标 | 数值 |
|------|------|
| 总文件数 | 546 |
| 风险文件 | 544 |
| 发现漏洞 | 0 |
| 严重漏洞 | 0 |
| 高危漏洞 | 0 |
| 中危漏洞 | 0 |
| 低危漏洞 | 0 |
| 确认漏洞 | 0 |
| 误报 | 0 |

## 侦察阶段结果

- **总文件数**: 546
- **风险文件**: 544
- **依赖数量**: 0

### 风险文件列表

| 文件路径 | 风险分数 | 风险原因 |
|----------|----------|----------|
| ai_config_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: config |
| ai_key_probe.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: key |
| content_feedback_loop.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: db |
| dacheng_keyword_seed_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: key |
| keyword_tracker.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: key |
| matrix_admin_bridge.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: admin |
| oauth_binding_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: auth |
| oauth_login.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: auth |
| super_admin_path_audit.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: admin |
| tenant_settings_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: settings |
| tenant_wecom_config_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: config |
| unified_admin_login.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: login |
| foreign_trade\matrix_oauth_publish_gate_service.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: auth |
| seo\seo_matrix_db_health.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: db |
| talking_stick\config.py | 90 | 源代码文件, 高风险文件类型, 敏感文件名: config |
| acme_service.py | 50 | 源代码文件, 高风险文件类型 |
| agent_aggregation_service.py | 50 | 源代码文件, 高风险文件类型 |
| agent_commission_service.py | 50 | 源代码文件, 高风险文件类型 |
| agent_hub_service.py | 50 | 源代码文件, 高风险文件类型 |
| agent_node_write_service.py | 50 | 源代码文件, 高风险文件类型 |

## 审计阶段结果

未发现漏洞

## 验证阶段结果

无验证结果

---
*报告由 Talking-Stick v1.0.0 自动生成*
