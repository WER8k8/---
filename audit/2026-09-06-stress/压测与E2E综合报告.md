# Docker 栈全量压测 + 浏览器 E2E 报告（2026-09-06）

> 环境：worktree `agents-install-vscode-cline-deploy-strix` Docker prod 栈（backend/frontend/postgres/redis + 8080 HTTP 代理）
> 租户：stress-a.local（pro 套餐），用户 tenant_demo/TenantDemo@2026!；管理员 admin/Admin123!
> LLM 网关：https://api.bankofai.io/v1（qwen3.8-flash / glm-5.3-flash）

## 一、结论总览

| 维度 | 结果 |
|---|---|
| API 压测（3 并发×3 轮=18 任务） | 18/18 PASS，p50=7.45s，p95=32.97s（真实 LLM 期间） |
| API 压测（6 并发×3 轮=18 任务） | 18/18 PASS，p50=8.31s，p95=27.03s；后端 CPU<1%、内存 1.4GiB/2GiB |
| 全量回归 | 22 套 *_verify.py 全部 rc=0（RLS 30/41、IDOR、wallet 15、task_chain 71 等） |
| 浏览器 E2E·文章/视频生成 | ✅ 弹窗→AI帮写→4步向导→提交→`media_render_tasks` 落库 done→列表可见 |
| 浏览器 E2E·智能体编排（财旺） | ✅ 出口可行性 19.2s 真实编排回复；找买家任务入队 `deerflow_jobs`（find_buyers/queued） |
| 数据隔离 | ✅ 压测 19 条视频任务全部归属租户 stress-a.local，无跨租户泄漏 |

## 二、本轮发现并修复的产品缺陷（4 个）

1. **CSRF double-submit 前端缺失（Cookie 认证模式下所有 POST 403）**
   - 根因链：登录后 `stores/auth.ts` ensureAuthInitialized 走 BFF userInfo 成功 → token 哨兵 `'cookie'` → `utils/api.ts authHeaders()` 不发 Bearer → 后端 `csrf_middleware.py` 落入 double-submit 分支 → 前端全库零处发 X-CSRF-Token → 403。
   - 修复：`utils/api.ts` 新增 `captureCsrfEchoToken`（GET 响应头 X-CSRF-Token 缓存到 sessionStorage）+ `authHeaders()` Cookie 模式回放。已实测：AI 帮写 POST 403→200。
2. **财旺浮窗发 `Bearer cookie` 被 401**
   - `UBrainAssistant.vue send()` 直接 `Authorization: Bearer ${tk}`，哨兵值成非法 Bearer。
   - 修复：哨兵 `'cookie'` 时改发 X-CSRF-Token + HttpOnly Cookie。实测修复后编排回复正常。
3. **`POST /api/v1/ubrain/chat` 路由函数漏写 return（响应体序列化为 null）**
   - `routes/ubrain.py ubrain_chat` 处理完 log_action 后无 return，FastAPI 返回 `null`，前端永远兜底"暂时无法回答"。
   - 修复：补 `return success_response(data=data)`。实测返回完整编排结果（intent=export_feasibility、SASO/SABER 合规分析、带会话记忆）。
4. **`views/products/edit.vue` script 块重复声明（Docker 构建必败）**
   - 同一 `<script setup>` 里 `const route` 声明两次且 import 穿插语句（疑似并行 agent 坏补丁）；本地构建侥幸通过、容器内 babel 严格报错。
   - 修复：合并 import 与声明，保留模板需要的 `productBase`。frontend 镜像构建恢复成功。

## 三、外部依赖故障（非本项目代码问题）

- **bankofai 密钥 `sk-1gp5…ynhf` 于 2026-09-06 03:46 UTC 起全端点 401**（"鉴权服务请求失败: Authentication failed"）。压测前段（03:37 前）同密钥可用（613 字符真实生成、8.9s）。宿主机 curl 直连网关同样 401，确认是网关侧密钥失效/额度回收，需商务续费或换新密钥。
- 失效后系统行为符合设计：`ai_engine.py generate()` 网关重试 3 次→本地模板降级（响应带 `【AI生成】` 前缀、mock 标记）；编排链路（意图→技能→规则库）不依赖网关，照常工作。

## 四、压测期间环境事件

- 04:46 UTC 整个 compose 栈被 SIGTERM 干净关停一次（backend/proxy/nginx-proxy Exit 0，原因未明，疑似外部 stop）；已 `docker compose up -d backend` + `docker start` 恢复，之后全链路复验通过。
- `docker ps --filter ancestor=python:3.12-slim` 误删事件的教训已在前次交接记录（backend 镜像基于 python:3.12-slim，清理时勿按 ancestor 过滤）。

## 五、遗留问题（未修，建议列入 ticket）

1. 公开站 `POST /api/v1/public/tenants/{domain}/wangcai/ask` 不在 CSRF 豁免清单——匿名访客无 csrf cookie 会被 403（公共端点设计缺陷）。
2. `inquiries` 表 FORCE RLS 导致公开 `/system/contact` 提交 500（未设置 app.current_tenant_id 的匿名连接被 RLS 拒绝）。
3. UBrain/超级智能体的 24 个 MCP 工具中仅 3 个真技能（customer_finder/auto_negotiator/email_automation），其余 stub；DeerFlow 工作流缺 `ai_engine` 包（`No module named 'ai_engine'`），workflow/start 500。
4. premium 模型（余额 0）不可用，仅 flash 档可用。

## 六、资产与复验入口

- 截图：`audit/2026-09-06-stress/e2e-wangcai-orchestration.png`（财旺编排对话）
- 压测脚本：`backend/tests/stress_generation_verify.py`（用法 `python tests/stress_generation_verify.py http://127.0.0.1:18000 <并发> <轮数>`）
- 租户种子：`backend/scripts/seed_stress_tenant.py`
- 入口：`http://127.0.0.1:8080`（HTTP 代理，绕开自签证书问题）；后端直连 `127.0.0.1:18000`
- 镜像：backend/frontend 均已用修复后的代码 `docker compose build` 重建并滚动替换，8080 全链 200

## 七、验证声明

本报告所有数字均为本轮实测（非历史沿用）：22 套回归 rc=0、压测 18+18+6 PASS、浏览器 E2E 两次全链（docker cp 部署 + 镜像化部署各一次）、PG log_statement 调试后已还原 none。
