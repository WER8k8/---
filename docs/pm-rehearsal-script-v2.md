# PM-03 · 送检脚本 v2 彩排指南

## 自动预检（彩排前）

```powershell
backend\.venv\Scripts\python.exe scripts\pm-rehearsal-v2-check.py
```

产出：`docs/pm-rehearsal-v2-check-latest.json`

## 现场 30min

1. 参与：PM · 前端 · 超管 · 租户(editor) · 代理(sales)
2. 按 [`送检演示脚本-v2-鉴定面.md`](./送检演示脚本-v2-鉴定面.md) 逐步操作
3. 截图已归档：[`cert-screenshots/`](./cert-screenshots/)（15 PNG）
4. 问题记录 → Gate 前关闭
5. 完成后更新 [`pm-l3-signoff.template.json`](./pm-l3-signoff.template.json)

## 账号（dev）

| 角色 | 用户 | 密码 |
|------|------|------|
| 超管 | admin | admin123 |
| 租户 | editor | editor123 |
| 代理 | sales | sales123 |

重置：`backend/scripts/seed_qa_passwords.py`
