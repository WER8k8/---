# SAAS-07 · 效果复盘表 v1

| 指标 | 定义 | 数据来源 |
|------|------|----------|
| 有效线索 | 含电话或邮箱且状态≠垃圾 | inquiries 表 |
| 有效电话 | 国际区号 + 号码校验通过 | inquiries.phone |
| 导出字段 | id, name, phone, email, source, created_at, status | `/international/inquiries` export |

复盘周期：周 · Owner：租户管理员
