# OpenCodeReview 全面检测报告 · 优丁工作树

- 工具：`alibaba/open-code-review` CLI **v1.12.5**（`ocr` 已全局安装）
- 规则源：`ocr rules check` 内置 Python 规则（精确优先、安全/正确性 blocking）
- LLM：**不可用**（NVIDIA `410 Gone`；Ollama 模型拉取 TLS 超时）→ 采用 **Delegation/宿主代理** 模式
- 扫描：`backend/app` + `backend/scripts`，文件 **1447**
- 发现合计 **594**（blocking 22 / major 338 / minor 234）
- 关键路径命中 **133** 条

## 按规则统计

| 规则 | 数量 |
|------|-----:|
| `silent-except` | 322 |
| `perf-log-fstring` | 234 |
| `security-sql-fstring` | 15 |
| `security-md5` | 10 |
| `resource-open` | 5 |
| `security-eval` | 4 |
| `security-shell` | 3 |
| `env-cwd-trap` | 1 |

## Blocking（须优先处理）

- **backend/app/core/login_bruteforce.py:200** · `security-eval` · 存在 eval/exec 调用
  - `pipe.eval(_LUA_RECORD, 1, _redis_key_id(ik),`
- **backend/app/core/login_bruteforce.py:202** · `security-eval` · 存在 eval/exec 调用
  - `pipe.eval(_LUA_RECORD, 1, _redis_key_ip(client_ip),`
- **backend/app/db/schema_healer.py:60** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `cursor.execute(f"PRAGMA table_info({table})")`
- **backend/app/db/schema_healer.py:92** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")`
- **backend/app/db/schema_healer.py:102** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `conn.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id {tenant_col}")`
- **backend/app/db/schema_healer.py:111** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")`
- **backend/app/services/acquisition/company_autofill.py:167** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `text(f"UPDATE companies SET {', '.join(sets)} WHERE id = :id"), params`
- **backend/app/services/ubrain/skill_audit_service.py:107** · `security-eval` · 存在 eval/exec 调用
  - `("exec(", "危险：动态代码执行", "high"),`
- **backend/app/services/ubrain/skill_audit_service.py:108** · `security-eval` · 存在 eval/exec 调用
  - `("eval(", "警告：动态表达式求值", "medium"),`
- **backend/app/services/talking_stick/agents/verify_agent.py:204** · `security-shell` · subprocess shell=True
  - `has_shell_true = "shell=True" in matched_content`
- **backend/scripts/check_density.py:21** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `cnt = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()`
- **backend/scripts/greenchain_p0b_verify.py:33** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `cur.execute(f"DROP DATABASE IF EXISTS {GREEN_DB} WITH (FORCE)")`
- **backend/scripts/greenchain_p0b_verify.py:34** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `cur.execute(f"CREATE DATABASE {GREEN_DB}")`
- **backend/scripts/greenchain_p0b_verify.py:131** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `conn.cursor().execute(f"DROP DATABASE {GREEN_DB} WITH (FORCE)")`
- **backend/scripts/opencodereview_host_detect.py:79** · `security-shell` · subprocess shell=True
  - `if "shell=True" in line or "shell = True" in line:`
- **backend/scripts/opencodereview_host_detect.py:80** · `security-shell` · subprocess shell=True
  - `add(path, i, "security-shell", "blocking", "subprocess shell=True", line)`
- **backend/scripts/patch_sqlite_content_pages.py:22** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `cur.execute(f"PRAGMA table_info({table})")`
- **backend/scripts/probe_code_slices.py:140** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `n = db.execute(text(f'select count(*) from "{tname}"')).scalar()`
- **backend/scripts/probe_db_engine.py:50** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `n = db.execute(text(f"select count(*) from {t}")).scalar()`
- **backend/scripts/probe_empty_tables_by_domain.py:87** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `n = db.execute(text(f'select count(*) from "{t}"')).scalar()`
- **backend/scripts/probe_pg_density.py:41** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `n = db.execute(text(f"select count(*) from {t}")).scalar()`
- **backend/scripts/seed_acquisition_main_chain_demo.py:51** · `security-sql-fstring` · SQL 使用 f-string 拼接风险
  - `return int(db.execute(text(f'select count(*) from "{table}"')).scalar() or 0)`

## 关键路径 Major（节选）

- **backend/app/core/admin_auth.py:266** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/core/config.py:115** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/oauth_login.py:318** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/payment_service.py:241** · `security-md5` · 使用 MD5（安全场景不推荐）
- **backend/app/services/payment_service.py:644** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/acquisition.py:740** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/acquisition_pipeline.py:151** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/client.py:225** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/client.py:362** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/domain.py:69** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/domain.py:270** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/domain.py:275** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/file_scans.py:72** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/inquiries.py:121** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/inquiries.py:711** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/mcp_sse.py:40** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/mobile_public.py:32** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/negotiation.py:259** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/negotiation.py:346** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/ops_aggregate.py:98** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:795** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:843** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:873** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:922** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:935** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/payment.py:991** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/public_tenant_geo.py:111** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/super_agent.py:842** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/super_agent.py:1136** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/tenants.py:1447** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/api/v1/routes/video_publish.py:219** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/billing_explain.py:114** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/billing_explain.py:137** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/company_autofill.py:211** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/company_autofill.py:218** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/dispatch_service.py:46** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/objection_copilot.py:210** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/onboarding.py:86** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/ops_card_pg.py:49** · `silent-except` · except 后直接 pass，错误被静默
- **backend/app/services/acquisition/ops_card_pg.py:56** · `silent-except` · except 后直接 pass，错误被静默

## 项目硬锁/一致性

- **env-cwd-trap** · backend/.env · env 声明 PG，但脚本 cwd≠backend 时会落到 SQLite（运行时陷阱）

## 如何复跑

```powershell
ocr --version
ocr rules check backend/app/services/acquisition/payment_risk.py
ocr scan --preview --repo . --path backend/app/services/hermes
# LLM 可用后：
ocr config set provider openai  # 或自定义
ocr scan --path backend/app/services/acquisition --format json -o docs/ocr-scan.json
```

机读全量：`docs/opencode-review-report.json`