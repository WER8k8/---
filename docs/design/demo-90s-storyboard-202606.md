# 90 秒融资 / 送检分镜（JD-02 · Owner 点验脚本）

> **依据**：`docs/youding-omni-pro-design-LOCKED.md` §10  
> **执行人**：Owner（业务）+ QA 录屏  
> **环境**：`scripts/start-dev-admin.ps1` · `admin / admin123`  
> **自动化门禁**：`powershell -File scripts/verify-step6-demo-gate.ps1`（2026-06-07 已通过）  
> **深色主题**：Slate Pro · Owner 已确认可用（60–70s 段重点看图标与三页卡片）

---

## 分镜表

| 时间 | 画面 | 操作（Owner 点） | 路由 | 失败即停 |
|------|------|------------------|------|----------|
| 0–15s | 登录 brand-hero | 打开 `/login` → 登录 | `/login` | placeholder 文案、第二套登录页 |
| 15–30s | Dashboard KPI | 侧栏「运营看板」或 `/admin/dashboard` | `/admin/dashboard` | KPI 假数无标注、卡片空白 |
| 30–35s | 进询盘 | 点击 Dashboard 待办 / 侧栏「询盘管理」 | `/inquiries` | 裸 `a-table`、无 YdPage |
| 35–50s | 租户列表 | 侧栏「租户管理」 | `/admin/tenants` | 列无居中、无 `--` 空值规范 |
| 50–60s | 列设置 / Drawer | 打开列设置或行内 Drawer | 同上 | 按钮无 handler |
| 60–70s | 主题抽屉 | 顶栏齿轮 → 暗色 + 换主色 | 任意 | **整页闪崩、侧栏双高亮** |
| 70–85s | Client 同壳 | 切租户角色或 `/client/dashboard` | `/client/dashboard` | 布局不一致、accent 未变 |
| 85–90s | Worktab 中文 | 任意再开 2 个菜单看标签名 | — | 标签英文 path、爆闪 |

---

## Owner 点验勾选（每次彩排填）

- [ ] 菜单切换仅 1 项高亮  
- [ ] Worktab 为侧栏中文名  
- [ ] 主题切换无白屏闪（浅色 ↔ Slate 深色）  
- [ ] 侧栏/顶栏图标清晰可见  
- [ ] 无「敬请期待」toast  

**自动化证据**：`docs/certification-gate-admin-latest.json` · `ready: true`  
**QA 走查**：`docs/qa/demo-rehearsal-walkthrough-20260607.md`（超管 + Client Pro Shell ✅）

**签字**：________ **日期**：________
