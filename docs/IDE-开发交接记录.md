# IDE 开发交接记录

> **最后同步**：2026-06-12  
> **源码仓**：`C:\Users\97907\Desktop\上线网站`  
> **出海计专项交接**：[`docs/出海计/开发交接记录-2026-06-12.md`](出海计/开发交接记录-2026-06-12.md)  
> **PM/产品补齐清单**：[`docs/出海计/PM-产品半完工补齐清单-2026-06-13.md`](出海计/PM-产品半完工补齐清单-2026-06-13.md)  
> **权威进度**：`docs/module-progress.json` · `docs/未完成开发任务表.md`

---

## 一、当前进度（一句话）

- **排期 Sprint A～O**：84/84（100%）  
- **产品模块权重**：**156/200（约 78%）**，还差 **44** 权重点  
- **本轮（2026-06-12）**：TTS 合成 API、超管工作台去假 KPI、物流运费公式、出海计 App 品牌标识 + 交接文档  
- **商用代码收尾**：实验室模块、真实 TTS/FCM、Capacitor 商店包（见任务表 §二、§三.b）

---

## 二、近期批次（2026-05-24～06-12）

| 批次 | 交付摘要 |
|------|----------|
| 1 | APP-0a mobile API、UBrain chat、trade_intel M0、app/home、Client 四支柱、PWA manifest |
| 2 | 迁移 023、trade_intel seed、Onboarding、devices/register |
| 3 | demo-checklist、push stub、platform-zones |
| 4 | `/agent` 壳、P0-08 超管路径对齐 |
| 5 | `/client/app` 四 Tab、sw.js、BFF config/today/assistant/chat、FCM 可选 |
| 6 | **UBrain-X Phase0**：5 获客工具、线索租户隔离、单测 10 passed |
| 7 | **UBrain-X P0**：`/client/copilot`、公开询盘手机必填、StickyImBar |
| 8 | **UBX-BE-03**：`lead_content_pack` → `content_masters` 草稿 |
| 9 | **UBX-AI-01**：`deerflow_jobs` + `/ubrain/jobs` |
| 10 | **P0-01/02**：ACME 刷新、`DEMO_HTTPS_DOMAIN` |
| 11 | **2026-06-12**：`POST /media-factory/tts/synthesize`、admin KPI 探针、logistics freight-calc、出海计交接记录 |

---

## 三、环境变量（功能开关）

| 变量 | 用途 |
|------|------|
| `FCM_SERVER_KEY` | 出海计真 Push（未设=stub） |
| `PAYMENT_STRICT_VERIFY` | 支付回调严格验签 |
| `SSL_PROVIDER` / `ACME_WEBHOOK_URL` | 独立域证书（acme/certbot/http/mock） |
| `DEMO_HTTPS_DOMAIN` | 保温厂演示独立域（P0-02 彩排） |
| `CERTBOT_EMAIL` / `CERTBOT_WEBROOT` | 本机 certbot 签发（P0-01） |
| `LOGISTICS_PROVIDER` | 物流（kuaidi100） |
| `API_HOST` | Nuxt 生产 API 基址 |
| `admin_lab_enabled` | 超管实验室菜单折叠 |

---

## 四、关键路由

| 端 | 路径 |
|----|------|
| 租户 App | `/client/app`（**出海计** PWA，非「出海记」） |
| UBrain | `POST /api/v1/ubrain/chat` |
| UBrain-X 卖货副驾 | `/client/copilot` |
| DeerFlow 任务 | `GET/POST /api/v1/ubrain/jobs/*` |
| HTTPS 演示域彩排 | `GET /api/v1/domain/pilot/demo-https` |
| App BFF | `/api/v1/app/v1/*` |
| 出海参谋 | `/api/v1/trade-intel/*` |
| 代理 | `/agent/dashboard` |
| 彩排 | `/admin/demo-rehearsal` |

---

## 五、验证命令

```powershell
cd backend
python -m pytest tests/unit/test_app_bff_batch5.py tests/unit/test_agent_portal.py tests/unit/test_ubrain_trade_intel.py -q
python scripts/module_progress.py
```

```powershell
cd "C:\Users\97907\Desktop\UJ\website CodeBuddy"
powershell -ExecutionPolicy Bypass -File scripts/sync-dev-docs-to-ides.ps1
```

---

## 六、下一优先

1. **实机**：配置 `DEMO_HTTPS_DOMAIN` + DNS + `scripts/pilot-acme-ssl-issue.ps1` 真签发  
2. **七步录屏**：访客询盘 → inquiries 带手机号 → 导出周报  
3. 保温厂按 `docs/出海计/保温厂-三平台发布SOP.md` 日更 1 条导站  
4. P0-03/06/07 与其余商用收尾（见任务表 §二）  
5. 改 `docs/` 后执行 `scripts/sync-dev-docs-to-ides.ps1`
