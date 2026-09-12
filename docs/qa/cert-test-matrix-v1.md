# QA-03 · 送检用例矩阵 v1

| ID | 角色 | 步骤 | 路由 | 期望 |
|----|------|------|------|------|
| Q1 | platform | 登录 | /login | 200 |
| Q2 | platform | 租户列表 | /admin/tenants | 表格可见 |
| Q3 | platform | 层级 | /admin/hierarchy | 无 hero-glass |
| Q4 | client | 工作台 | /client/dashboard | Bento 首屏 |
| Q5 | client | 询盘 | /client/inquiries | inbox |
| Q6 | agent | 业绩 | /agent/performance | 白底 KPI |
| Q7 | agent | 无超管链 | /agent/* | 无 /admin 链接 |
| Q8 | platform | 送检菜单 | cert mode | ≤鉴定面 |

对齐：[`送检演示脚本-v2-鉴定面.md`](../送检演示脚本-v2-鉴定面.md)
