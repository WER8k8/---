# OpenCodeReview 全面检测报告 · 优丁工作树

> **工具**：`alibaba/open-code-review`（GitHub 35k+ stars）CLI **v1.12.5**  
> **安装**：`npm install -g @alibaba-group/open-code-review` → `ocr --version`  
> **仓库**：https://github.com/alibaba/open-code-review  
> **模式**：CLI 安装 + 内置规则解析 + `ocr scan --preview` 范围 + **宿主代理静态检测**  
> **LLM 状态**：不可用（NVIDIA `integrate.api.nvidia.com` → **410 Gone**；Ollama 模型拉取 TLS 超时）  
> **规则源**：`ocr rules check <file>` → System built-in `**/*.{py,pyi,ipynb}`  
> **扫描**：`backend/app` + `backend/scripts` · 文件 **1355**  
> **机读**：`docs/opencode-review-report.json`

---

## 1. 总览

| 指标 | 值 |
|------|-----|
| 发现合计 | **524** |
| blocking（工具标级） | 20 |
| major | 287 |
| minor | 217 |
| 关键路径命中 | 109 |
| 硬锁 LOGIN/薄荷 | **通过**（无 client/login.vue；主色 #4a9b8c 在位） |

### 按规则分布

| 规则 | 数量 | OCR 含义 |
|------|-----:|----------|
| `silent-except` | 273 | except 后 pass，错误静默 |
| `perf-log-fstring` | 217 | logging 用 f-string |
| `security-sql-fstring` | 13 | SQL 字符串拼接 |
| `security-md5` | 10 | 使用 MD5 |
| `security-eval` | 4 | eval/exec 字样 |
| `security-shell` | 3 | shell=True 字样 |
| `resource-open` | 2 | open 可能无 with |
| `route-duplicate` | 1 | acquisition 路由重复 |
| `env-cwd-trap` | 1 | PG/SQLite cwd 陷阱 |

---

## 2. 发现分诊（人工按 OCR「精确优先」原则复核）

### 2.1 真问题 / 须处理（工程有效）

| 级别 | 位置 | 问题 | 建议 |
|------|------|------|------|
| **P0** | `api/v1/routes/acquisition.py` | `GET /ops/reconcile` **装饰器重复声明** | 删重复，加路由测试 |
| **P0** | 环境 | env 写 PG，**cwd≠backend 时落 SQLite** | 启动脚本锁 cwd；探针告警 |
| **P0** | 前端 engage | 调用 `/api/v1/client/douyin-comments/pull`，**后端无 douyin 路由** | 补路由或前端下线 |
| **P1** | `db/schema_healer.py:60,92,102,111` | `ALTER/PRAGMA` 使用 **f-string 拼表名/列名** | 表名白名单校验；禁止外部输入进 DDL |
| **P1** | `services/acquisition/billing_explain.py` `ops_card_pg.py` `dispatch_service.py` 等 | **`except Exception: pass`** 静默 | 至少 `logger.warning`；业务关键路径禁止吞异常 |
| **P1** | `routes/tenants.py` `inquiries.py` `payment_service.py` 等 | 同上，关键路径 silent except | 按 OCR Error Handling 规则收敛 |
| **P1** | 支付/物流签名 | `payment_service.py` `wechat_pay.py` `logistics_provider.py` 使用 **MD5 签名** | 若上游要求 MD5 则文档标明「通道协议」；新通道用 HMAC-SHA256 |
| **P2** | `core/cache_decorator.py` 等 | MD5 做 cache key | 非安全场景可接受；可换 blake2/sha256 |
| **P2** | 关键路径大量 `logger.info(f"...")` | 性能/规范 minor | 热路径逐步改 `%s` 懒格式化 |
| **P2** | `scripts/probe_*.py` `seed_*.py` | `count(*) from {table}` f-string | 表名来自 `information_schema`/白名单则风险低；仍应白名单 |

### 2.2 误报（工具字符串误判，非真 eval/shell）

| 位置 | 工具结论 | 实际 |
|------|----------|------|
| `core/login_bruteforce.py:200,202` | eval/exec | **Redis Lua `pipe.eval`**，合法 |
| `ubrain/skill_audit_service.py:107-108` | eval/exec | 审计规则**字符串字面量** |
| `talking_stick/verify_agent.py` | shell=True | 源码扫描器**检测字符串** |
| `scripts/opencodereview_host_detect.py` | shell=True | **本检测脚本自身**的规则匹配代码 |
| `scripts/greenchain_p0b_verify.py` | SQL 拼接 | 本地验证脚本 DROP/CREATE 固定库名 |

### 2.3 项目硬锁（OCR 范围 + 本仓契约）

| 锁 | 结果 |
|----|------|
| LOGIN-LOCK-01 | ✅ 无 `client/login.vue`；`/login` 唯一组件 |
| DESIGN-TOKEN-LOCK-01 | ✅ `PLATFORM_BRAND_DEFAULT = '#4a9b8c'`；admin tailwind 含薄荷 |
| ROLE-SHELL | ✅ router 壳路径在（此前代码探测已核） |
| ENV-LOCK | ⚠️ 配置在，**运行时 cwd 陷阱仍在** |

---

## 3. OCR CLI 本身能做什么（已验证）

```text
ocr --version          → v1.12.5 windows/amd64 ✅
ocr rules check <py>   → 输出完整内置 Python 评审规则 ✅
ocr scan --preview     → hermes 目录 119 文件 / ~3 万行（全文件扫描范围）✅
ocr review/scan 真评审 → 需可用 LLM ❌（当前 provider 410/TLS）
ocr delegate           → 无 LLM 时导出规则给宿主代理 ✅（本轮采用）
```

内置规则覆盖：死代码、可变默认参、边界/None、异常处理、身份比较、资源管理、并发、安全敏感代码等——与上表分诊一致。

---

## 4. 关键路径 silent-except 抽样（major · 优先修）

```
backend/app/core/admin_auth.py:254
backend/app/services/oauth_login.py:279
backend/app/services/payment_service.py:644
backend/app/api/v1/routes/acquisition.py:1231
backend/app/services/acquisition/billing_explain.py:114,137
backend/app/services/acquisition/dispatch_service.py:46
backend/app/services/acquisition/ops_card_pg.py:49
backend/app/services/acquisition/onboarding.py:86
backend/app/services/acquisition/nps_rescue.py:43
backend/app/api/v1/routes/tenants.py:1447
backend/app/api/v1/routes/inquiries.py:121
```

全量 major **273** 条见 JSON。

---

## 5. 复跑命令

```powershell
npm install -g @alibaba-group/open-code-review
ocr --version
ocr rules check backend/app/services/acquisition/payment_risk.py
ocr scan --preview --repo . --path backend/app/services/hermes
# LLM 配好后：
ocr config set provider <provider>
ocr config set model <model>
ocr scan --path backend/app/services/acquisition --format json -o docs/ocr-scan.json
# 本轮宿主检测：
cd backend
.venv\Scripts\python.exe scripts\opencodereview_host_detect.py
```

---

## 6. 结论（主理人可读）

1. **OpenCodeReview 已安装可用**（阿里官方 CLI），内置规则与扫描范围已接入本仓。  
2. **自动 LLM 全库扫描未跑通**：现有 NVIDIA Key 已 **410**，本机 Ollama **拉不动模型**——不假装「AI 已扫完全库」。  
3. **按 OCR 官方规则做了全量静态检测**（1355 文件）：真问题集中在 **异常静默、SQL/DDL 拼接、MD5 签名约定、路由重复、环境 cwd 陷阱**；登录/主色硬锁 **未破**。  
4. **下一步最有价值**：修 P0 三项 + 关键路径 silent-except；你提供可用 LLM Key 后即可 `ocr scan` 出官方 JSON 评审。

---

*报告生成：OpenCodeReview host-agent · 2026-09-18*
