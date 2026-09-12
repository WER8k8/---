# 90 秒送检 · QA 彩排走查记录（JD-02 / WP-QA-DEMO-01）

> **日期**：2026-06-07  
> **环境**：`http://127.0.0.1:5173` · API `:8001` · 已登录超管  
> **自动化前置**：`scripts/verify-step6-demo-gate.ps1` → `ready: true`

---

## 分镜走查结果


| 时间     | 路由                  | 结果  | 说明                                                               |
| ------ | ------------------- | --- | ---------------------------------------------------------------- |
| 0–15s  | `/login`            | ✅   | 单入口；会话已存在时自动进壳                                                   |
| 15–30s | `/admin/dashboard`  | ✅   | YdPage + KPI + 待办链 `/inquiries`；深色 Slate 正常                      |
| 30–50s | `/inquiries`        | ✅   | YdPage · 列设置 · 「更多」含导出 · 无裸主列表                                   |
| 35–50s | `/admin/tenants`    | ✅   | YdPage · 搜索 · 列设置 · Drawer                                       |
| 50–60s | 列设置/Drawer          | ✅   | 租户/询盘页具备列设置入口                                                    |
| 60–70s | 主题抽屉                | ✅   | 顶栏「主题与布局」可用；深色切换无白屏（走查时已在深色）                                     |
| 70–85s | `/client/dashboard` | ✅   | **已接入 Pro Shell**（侧栏/顶栏/Worktab 与超管同构，Client 蓝 accent） |
| 85–90s | Worktab             | ✅   | 标签为中文（如「询盘留言」「SaaS租户」），非 path 英文                                 |


---

## Owner 勾选（QA 代填 · 待 Owner 签字确认）

- 菜单切换仅 1 项高亮（走查未见双高亮）
- Worktab 为侧栏中文名
- 主题切换无白屏闪（深色已验收）
- 侧栏/顶栏图标清晰可见
- 无「敬请期待」toast

**待 Owner**：正式 **90 秒录屏** + 底部签字（Client 壳已统一，可正常走 70–85s 分镜）。

---

## 关联页

- 彩排清单 UI：`/admin/demo-rehearsal`（API 探针 pass 10 · warn 5 · fail 0 · development）
- 七步商用探针：step 2「独立域 HTTPS」fail — 缺 `DEMO_HTTPS_DOMAIN` 环境变量，**不阻断 Admin UI 送检**

---

## 证据文件

- `docs/certification-gate-admin-latest.json`
- 分镜脚本：`docs/design/demo-90s-storyboard-202606.md`

**QA 签字**：________ **Owner 签字**：__继续

______