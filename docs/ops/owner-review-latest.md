# Owner 催办 · COMM-PM-02（2026-06-14）

> **签发**：PM-07 · Sprint-COMM-1 W1  
> **研发状态**：7/7 Lane 全绿 · `cert:gate` 绿 · `validate-no-fake-delivery` P0=0  
> **以下三项须 Owner 拍板，研发无法代签**

---

## O-1 · HTTPS 演示独立域

| 项 | 状态 |
|----|------|
| 技术清单 | ✅ `scripts/pilot-acme-ssl-issue.ps1` + `backend/config/prod/.env.example`（`DEMO_HTTPS_DOMAIN`） |
| DNS / 域名 | ⬜ **待 Owner** |
| 阻塞 | `COMM-QA-02` 七步截图 · `MOD-04` 录屏 · `MOD-01` 实签发 |

**请您提供**：演示用 FQDN（如 `demo.xxx.com`）+ DNS 指向 staging/生产入口。

---

## O-2 · 询盘 IM 生产密钥 / 企微

| 项 | 状态 |
|----|------|
| 后台配置页 | ✅ `/inquiries/im-routing`（5a/5b/5c 链） |
| 租户站 StickyImBar | ✅ 手机必填 · 无假渠道回退（P1-01） |
| 生产 CorpID/Secret | ⬜ **待 Owner/客户** |

**阻塞**：`ITER-03c` staging 三张截图 · `MOD-02` 生产 handoff

---

## O-3 · 5+5 平台表 + 套餐价签字

| 项 | 状态 |
|----|------|
| 清单与 checklist | ✅ `docs/pm-owner-blockers-20260604.md` |
| 价表 / 平台矩阵签字 | ⬜ **待 Owner** |

**阻塞**：`MOD-03` · `MOD-08` · 对外报价话术

---

## 下一轮站会（研发可并行）

- `COMM-PM-03` Stub Kill 评审（6/18，产品主持）
- `COMM-PD-01` 送检清单 V1.1 签字
- `COMM-VIS-01` JD-01 三 accent 签认

*PM-07 更新 · 与 `pm-dispatch-latest.json` 同步*
