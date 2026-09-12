# 双 Admin 回滚 Runbook（ARCH-02）

> **目标**：10 分钟内从 Vben 切回现网 `frontend/admin`

## 触发条件

- Vben BFF 登录失败且 S0 送检临近
- cert:gate 回归失败仅 Vben 分支

## 步骤

1. **DNS / Nginx**：静态入口指回 `frontend/admin` 构建产物（端口 5173 dev / dist prod）
2. **环境变量**：`VITE_USE_BFF=false`（现网默认仍 `/api/v1/auth/login`）
3. **验证**：送检脚本 v2 走现网 admin · 12 路由 200
4. **记录**：在 `ecc-delivery-tracker.md` 标注回滚时间与原因

## 演练清单

- [x] BFF 冒烟 `scripts/qa-three-shell-e2e.py`
- [x] 送检路由 `npm run cert:nav`
- [x] 自动化脚本 `scripts/arch-02-rollback-drill.ps1`
- [ ] 现网 `npm run build` 成功（已知 TS 债务项除外）
- [ ] Nginx 切回 dist 实机（人工）

*ARCH-02 v1 · W2 演练*
